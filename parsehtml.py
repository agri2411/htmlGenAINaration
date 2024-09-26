import sys
import json
from bs4 import BeautifulSoup
from google.cloud import bigquery
import google.generativeai as genai
import os
import http.server
import socketserver
import pandas as pd
import dbQry as dQ
from dotenv import load_dotenv
from pathlib import Path
# Set your OpenAI API key
# openai.api_key = os.getenv("OPENAI_API_KEY")

# def generate_summary(table_content):
#     prompt = f"Summarize the following table content:\n\n{table_content}\n\nSummary:"
#     response = openai.Completion.create(
#         engine="text-davinci-002",
#         prompt=prompt,
#         max_tokens=150,
#         n=1,
#         stop=None,
#         temperature=0.7,
#     )
#     return response.choices[0].text.strip()

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

def generate_summary(table_content):
# Set up your Google Cloud credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv('GCP_JSON_PATH')
    genai.configure(api_key=os.getenv('BQ_API_KEY'))  
    client = bigquery.Client()

    query = dQ.summary

    query_job = client.query(query)
    results = query_job.result()
    df = pd.DataFrame(results)  # More efficient than the list comprehension


    prompt = f"Summarize the following table content:\n\n{table_content}\n\nSummary:"
    model = genai.GenerativeModel('gemini-pro')
    generation_config = {
        "max_output_tokens": 250,
        "temperature": 1,
        "top_p": 0.95
    }
    response = model.generate_content(prompt,
        generation_config=generation_config
        # ,safety_settings=
        # stream=True
        ) 
    
    # HTML formatting 
    # response_text_modified = response.text.replace("*", "")

    # print(html.replace("<li></li>", ""))  
    return response.text
    # html.replace("<li></li>", "")

class SummaryHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        html_table = data['table']
        soup = BeautifulSoup(html_table, 'html.parser')
        table_content = soup.get_text()
        summary = generate_summary(table_content)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'summary': summary}).encode())

def do_GET(self):
    if self.path == '/':
        self.path = 'index.html'
    return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), SummaryHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()