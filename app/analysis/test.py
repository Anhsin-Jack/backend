# import sys
# sys.path.append("/Users/michaelchee/Documents/backend/app/analysis")
# import utils
# from text2sql import Text2SQL
# text2sql = Text2SQL()
# query = "What are the average prices of each product?"
# company_description = "The company is Nike."
# analysis_steps = utils.generate_analysis_steps(query,company_description)
# print("Analysis Steps: ",analysis_steps)
# sql_query = text2sql.get_sql_query(analysis_steps,company_description)
# print("SQL Query: ",sql_query)

from cryptography.fernet import Fernet

# Generate a random 256-bit (32-byte) key
key = Fernet.generate_key()

# Print and use this key in your application
print("Secret Key:", key.decode())

