import sys, re, contextlib, io, base64, boto3, datetime, uuid
import pandas as pd
import matplotlib.pyplot as plt
from botocore.exceptions import NoCredentialsError
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from .llms import use_openai
from . import prompts
import asyncio, json, pytest, time


async def test_streamimg(query:str):
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": query}
    ]
    full_response = ""
    for response in use_openai(model="gpt-3.5-turbo",message=messages,temperature=0,stream = True):
        if response.choices[0].delta.content != None:
            # Iterate through and display each chunch
            full_response += response.choices[0].delta.content
        return_response = full_response +"▌ "
        yield f"data: {return_response}\n\n"
        await asyncio.sleep(0.5)
    yield f"data: {full_response}\n\n"

async def get_recommendation(query:str, analysis_results:str,industry:str,language:str):
    system_message = prompts.get_recommendation_system_message(analysis_results,industry,language)
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]
    full_response = ""
    for response in use_openai(model="gpt-4-1106-preview",message=messages,temperature=0,stream = True):
        # Iterate through and display each chunch
        full_response += response.choices[0].delta.content
        return_response = full_response +"▌ "
        yield f"data: {return_response}\n\n"
        await asyncio.sleep(0.1)
    yield f"data: {full_response}\n\n"

def generate_analysis_steps(query:str, company_description:str):
    system_message = prompts.get_analysis_steps_system_message(company_description)
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]
    response = use_openai(model="gpt-3.5-turbo",message=messages,temperature=0)
    return response

def get_distinct_values_df(df:pd.DataFrame)->str:
    column_content = ""
    for column in df.columns:
        distinct_values = df[column].unique().tolist()
        try:
            minimum = df[column].min()
            maximum = df[column].max()
        except Exception:
            minimum = None
            maximum = None
        if minimum and maximum and 0<len(distinct_values)<20:
            column_content += f"The column name is \"{column}\" with distinct values: {distinct_values} , and range: [{minimum},{maximum}]\n"
        else:
            if 0<len(distinct_values)<20:
                column_content += f"The column name is \"{column}\" with distinct values: {distinct_values}\n"
    return column_content

def extract_codes(analysis_code:str)->str:
    # Define a regular expression pattern to match Python code blocks
    pattern = r'```python(.*?)```'
    # Use the re.findall function to extract Python code blocks
    code_blocks = re.findall(pattern, analysis_code, re.DOTALL)
    codes = "\n".join(code_blocks)
    return codes

def upload_bytes_to_s3(bytes_data, file_extension):
    """
    Upload bytes data to an Amazon S3 bucket and return the public link to the uploaded file.

    This method uses the Amazon Web Services (AWS) S3 client to upload the provided bytes data to a specified
    S3 bucket. It generates a unique filename, uploads the data, and returns a public link to the uploaded file.

    Parameters:
    - bytes_data: The bytes data to be uploaded.
    - file_extension: The file extension for the uploaded file.

    Returns:
    - link (str): The public link to the uploaded file.

    Example usage:
    assistant = YourAssistantClass()
    data = b"Binary data here..."
    extension = "png"
    upload_link = assistant.upload_bytes_to_s3(data, extension)
    print("Uploaded file link:", upload_link)
    """
    from config import settings
    link = ""
    try:
        s3 = boto3.client('s3', aws_access_key_id=settings.aws_access_key, aws_secret_access_key=settings.aws_secret_key)
        
        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # Generate a unique identifier
        unique_identifier = str(uuid.uuid4())
        
        # Create a new filename with the unique identifier and file extension
        unique_file_name = f"{timestamp}_{unique_identifier}.{file_extension}"
        
        # Upload the bytes data
        s3.put_object(Bucket=settings.aws_bucket_name, Key=unique_file_name, Body=bytes_data, ACL='public-read')
        
        link = f"https://{settings.aws_bucket_name}.s3.amazonaws.com/{unique_file_name}"
        print("Upload Successful")
    except NoCredentialsError:
        print("Credentials not available")
    return link

def execute_code(code:str, local_variable:dict):
    """
        This function is to execute a string which contains full of code and then get the print results, and local variables.
        Input:
            code (str): A string contains Python Code.
            local_variable (dict): A dictionary contains local variables to execute code.
        Output:
            (dict) A dictionary which filtered all the local variables.
    """
    final_print_outputs = []
    plots = []
    try:
        code = "\n".join([line for line in code.split("\n") if "plt.show()" not in line])
        pattern_to_remove = r'.*print.*df.*'
        code_lines = code.split("\n")
        filtered_code_lines = [line for line in code_lines if not re.match(pattern_to_remove, line)]
        code = '\n'.join(filtered_code_lines)
        # Capture output using contextlib.redirect_stdout
        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            exec(code, local_variable)
        # Filter local_variable
        filtered_variables = {
            var_name: var_value
            for var_name, var_value in local_variable.items()
            if not var_name.startswith("__")
        }
        dataframes = []
        for _ , value in filtered_variables.items():
            if isinstance(value, pd.DataFrame) or isinstance(value, pd.Series):
                str_value = value.to_string()
                print(str_value)
                dataframes.append(str_value)

        # Get captured output and add to the list
        output_list = captured_output.getvalue().strip().split("\n")
        # Variables to accumulate outputs and plots
        if "plt." in code:
            # Create base64-encoded images of all plotted figures
            fignums = plt.get_fignums()
            for i, fig in enumerate(fignums):
                plt.figure(fig)
                if "plt.tight_layout()" not in code:
                    plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                plt.close(fig)
                buf_value = buf.getvalue()
                image_link = upload_bytes_to_s3(buf_value, "png")
                if image_link:
                    plots.append(image_link)
        if output_list:
            # Display each item in the output list
            for item in output_list:
                if "dtype" not in item:
                    final_print_outputs.append(item)
                # is_display = True
                # for dataframe in dataframes:
                #     if item in dataframe:
                #         is_display = False
                #         break
                # if is_display:
                #     final_print_outputs.append(item)
    except Exception as e:
        print(e)
        filtered_variables = {}
        print("Execute code error: ", str(e))
    return filtered_variables, "\n".join(final_print_outputs), plots


def analyse(query:str,df:pd.DataFrame,company_description:str,analysis_step:str):
    df_head = df.head().to_string()
    column_content = get_distinct_values_df(df)
    system_message = prompts.get_analysis_code_system_message(company_description, column_content,df_head,analysis_step)
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]
    response = use_openai(model="gpt-4-1106-preview",message=messages,temperature=0)
    codes = extract_codes(response)
    variables, prints, plots = execute_code(codes, {"df":df})
    return [variables, prints, plots]

async def get_analysis_recommendation(query:str,data:dict, company_description:str,analysis_steps:str, language:str):
    df = pd.DataFrame(data)
    results = analyse(query,df,company_description,analysis_steps)
    #variables, prints, plots
    if results[2]:
        yield f"data: {json.dumps(results[2])}\n\n"
    if results[1]:
        yield f"data: {results[1]}\n\n"
    system_message = prompts.get_recommendation_system_message(results[0],company_description,language)
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]
    full_response = ""
    for response in use_openai(model="gpt-4-1106-preview",message=messages,temperature=0,stream = True):
        if response.choices[0].delta.content != None:
            # Iterate through and display each chunch
            full_response += response.choices[0].delta.content
            return_response = full_response +"▌ "
            yield f"data: {return_response}\n\n"
            await asyncio.sleep(0.1)
    yield f"data: {full_response}\n\n"

@pytest.mark.asyncio
async def test_get_analysis_recommendation():
    # _ = utils.authentication(access_token,db)
    import json

    # Assuming your JSON file is named 'example.json'
    file_path = 'output.json'

    # Read JSON file
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)

    query = "What are the average prices of each product?"
    company_description = "The company is Nike."
    analysis_steps = ""
    language = "English"

    async for response in get_analysis_recommendation(query, data, company_description, analysis_steps, language):
        print(response)

if __name__ == "__main__":
    pass
    # pytest.main()

    # from text2sql import Text2SQL
    # text2sql = Text2SQL()
    # query = "What are the average prices of each product?"
    # company_description = "The company is Nike."
    # analysis_steps, sql_query = text2sql.get_sql_query(query,company_description)
    # print("SQL Query: ")
    # print(sql_query)
    # engine = text2sql.engine
    # df = pd.read_sql(sql_query,engine)
    # json_data = df.to_json(orient='records')
    # # Write JSON to a file
    # with open('output.json', 'w') as json_file:
    #     json_file.write(json_data)
    # variables, prints, plots = analyse(query,df,company_description,analysis_steps)
    # print("Variables: ")
    # print(variables)
    # print("Prints: ")
    # print(prints)
    # print("Plots: ")
    # print(plots)
    # print("Recommendation:")
    # get_recommendation_no_stream(query,variables,company_description,"English")