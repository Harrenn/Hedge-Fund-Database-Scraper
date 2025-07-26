from flask import Flask, render_template, request, Response
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

def scrape_hedge_funds(url, num_rows):
    """
    Scrapes the hedge fund database table from buysidedigest.com.

    Args:
        url (str): The URL of the hedge fund database page.
        num_rows (int): The number of rows to scrape. If 0, scrapes all rows.

    Returns:
        list: A list of dictionaries containing the scraped data, or None if an error occurs.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to retrieve the webpage. {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', id='md-fund-letter-table')

    if not table:
        return None

    rows = table.find_all('tr', class_='md-fund-table-row')
    
    if not rows:
        return None

    if num_rows > 0:
        rows_to_process = rows[:num_rows]
    else:
        rows_to_process = rows

    fund_data = []
    for row in rows_to_process:
        cells = row.find_all('td')
        if len(cells) > 8:
            fund_name = cells[1].get_text(strip=True)
            letter_cell = cells[8]
            letter_link_tag = letter_cell.find('a')
            letter_link = letter_link_tag['href'] if letter_link_tag else 'N/A'
            fund_data.append({
                'Fund Name': fund_name.replace("'", ""),
                'Letter Link': letter_link,
                'Download Link': letter_link
            })

    return fund_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        num_rows = request.form.get('num_rows', 0, type=int)
        base_url = "https://www.buysidedigest.com/hedge-fund-database/"
        data = scrape_hedge_funds(base_url, num_rows)
        
        if data:
            return render_template('index.html', data=data, rows_requested=True)
        else:
            return render_template('index.html', error="Could not scrape data. The website structure may have changed or the site is temporarily unavailable.", rows_requested=True)
            
    return render_template('index.html', data=None, rows_requested=False)

@app.route('/download')
def download_file():
    file_url = request.args.get('url')
    fund_name = request.args.get('fund_name', 'download') # Default to 'download' if not provided
    if not file_url:
        return "Error: No URL provided.", 400

    try:
        r = requests.get(file_url, stream=True)
        r.raise_for_status()
        
        # Sanitize the filename and add .pdf extension
        filename = "".join(c for c in fund_name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{filename}.pdf"
        
        return Response(
            r.iter_content(chunk_size=1024),
            mimetype='application/pdf',
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\""
            }
        )
    except requests.exceptions.RequestException as e:
        return f"Error: Could not download file. {e}", 400

if __name__ == '__main__':
    app.run(debug=True)
