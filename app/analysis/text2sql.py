import re, json
from time import time
from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from analysis import prompts, llms, utils
from config import settings

    
class Text2SQL():    
    def __init__(self):
        self.db_uri = f"mysql+pymysql://{settings.database_user}:{settings.database_password}@{settings.database_host}/{settings.database_name}"
        self.engine = create_engine(self.db_uri)
    def get_table_column(self, engine: Engine) -> str:
        inspector = Inspector.from_engine(engine)
        tables = inspector.get_table_names()
        formatted_table_info = ""
        primary_key = " (PRIMARY KEY)"
        foreign_key = " (FOREIGN KEY)"
        for table in tables:
            columns = [column["name"] for column in inspector.get_columns(table)]
            primary_key_info = inspector.get_pk_constraint(table)
            primary_keys = primary_key_info['constrained_columns']
            if primary_keys:
                    for key in primary_keys:
                        if key in columns:
                            index = columns.index(key)
                            columns[index] = key + primary_key
            foreign_keys = inspector.get_foreign_keys(table)
            for key in foreign_keys:
                referred_table = key["referred_table"]
                key_name = key["constrained_columns"][0]
                if key_name in columns:
                    index = columns.index(key_name)
                    columns[index] = key_name + foreign_key + f", referred_table: {referred_table})"                           
            column_names = ", ".join(columns)
            formatted_table_info += f"(The table name is : '{table}', column header names of '{table}' table are: {column_names})\n"
        return formatted_table_info
    
    def get_column_attributes(self, engine: Engine) -> str:
        inspector = Inspector.from_engine(engine)
        tables = inspector.get_table_names()
        print("Get Column Attributes: ",tables)
        formatted_column_attributes = ""
        for table in tables:
            columns = [[column["name"],column["comment"]] for column in inspector.get_columns(table)]
            formatted_column_attributes += f"The table name is : '{table}', column header names of '{table}' table and column attributes are:\n"
            for column in columns:
                formatted_column_attributes += f"(The column name is '{column[0]}' : The attribute of this column is '{column[1]}')\n"
            formatted_column_attributes += "\n"
        return formatted_column_attributes
    def modified_sql_query(self,sql_query:str):
        sql_pattern = r"```sql(.*?)```"
        match = re.search(sql_pattern, sql_query, re.DOTALL)
        if match:
            # Extract the matched SQL query
            sql_query = match.group(1).strip()
            modified_sql_query = sql_query.replace("%","%%").replace("\n"," ")
            return modified_sql_query
        return ""
    def get_sql_query(self, query: str, company_description: str) -> str:
        try:
            analysis_steps = utils.generate_analysis_steps(query, company_description)
            table_info = self.get_column_attributes(self.engine)
            system_message  = prompts.get_text2sql_system_message(company_description, table_info)
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": analysis_steps}
            ]
            sql_query = llms.use_openai(model="gpt-4-1106-preview",message=messages, temperature=0)
            """Modify SQL Query"""
            modified_sql_query = self.modified_sql_query(sql_query)
            return analysis_steps, modified_sql_query
        except Exception as e:
            return "", f"Error: {str(e)}"
    
    def is_database_modifying_query(self, sql_query: str) -> bool:
        modifying_keywords = ['INSERT', 'UPDATE', 'DELETE', 'ALTER', 'CREATE', 'DROP', 'TRUNCATE']
        modifying_statements = ['INSERT INTO', 'UPDATE', 'DELETE FROM', 'ALTER TABLE', 'CREATE', 'DROP', 'TRUNCATE']
        try:
            """Normalize the query and remove extra spaces"""
            normalized_query = ' '.join(sql_query.strip().split())

            """Check for modifying keywords"""
            for keyword in modifying_keywords:
                if keyword in normalized_query:
                    return True

            """Check for modifying statements"""
            for statement in modifying_statements:
                if re.search(r'\b' + re.escape(statement) + r'\b', normalized_query, re.IGNORECASE):
                    return True
        except Exception as e:
            return False
        return False
    