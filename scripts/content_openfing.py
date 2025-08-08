import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURATION ---
BASE_URL = "https://open.fing.edu.uy/courses/"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
JSON_FILE = r"..\backend\scraping\ScrapInfo\CoursesAcronyms.json"

def getCourseListContent():
    content_json = []
    
    try:
        # Fetch the main course list page
        response = requests.get(BASE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the course list div
        course_list_div = soup.find('div', class_='course-list')
        if not course_list_div:
            print("Course list div not found")
            return []
        
        # Process each course link
        for a_tag in course_list_div.find_all('a', href=True):
            course_data = {
                'title_a': a_tag.get_text(strip=True),
                'acronym': a_tag['href'].replace(BASE_URL, '').strip('/'),
                'subcourses': []
            }
            
            # Visit the course page
            course_url = a_tag['href']
            try:
                course_response = requests.get(course_url)
                course_response.raise_for_status()
                course_soup = BeautifulSoup(course_response.text, 'html.parser')
                
                # Get main title
                h1_tag = course_soup.find('h1')
                course_data['title'] = h1_tag.get_text(strip=True) if h1_tag else None
                
                # Get subtitle
                subtitle_tag = course_soup.find('a', class_='related-links__item related-links__item--active')
                course_data['subtitle'] = subtitle_tag.get_text(strip=True) if subtitle_tag else None
                
                # Get classes and URLs
                course_data['classes'] = []
                course_data['urls'] = []
                
                for class_item in course_soup.find_all('a', class_='class-list__item'):
                    class_url = class_item['href']
                    class_number = class_item.find('span', class_='class-list__item-number')
                    
                    if class_number:
                        course_data['classes'].append(class_number.get_text(strip=True))
                        mp4_url = get_mp4_url(class_url)
                        if mp4_url:
                            course_data['urls'].append(mp4_url)
                
                # Process subcourses
                for subcourse_link in course_soup.find_all('a', class_='related-links__item'):
                    if 'related-links__item--active' in subcourse_link.get('class', []):
                        continue
                    
                    subcourse_url = subcourse_link['href']
                    try:
                        subcourse_response = requests.get(subcourse_url)
                        subcourse_response.raise_for_status()
                        subcourse_soup = BeautifulSoup(subcourse_response.text, 'html.parser')
                        
                        subcourse_data = {
                            'acronym': subcourse_link['href'].replace(BASE_URL, '').strip('/'),
                            'subtitle': subcourse_link.get_text(strip=True),
                            'classes': [],
                            'urls': []
                        }
                        
                        # Get classes for subcourse
                        for class_item in subcourse_soup.find_all('a', class_='class-list__item'):
                            class_url = class_item['href']
                            class_number = class_item.find('span', class_='class-list__item-number')
                            
                            if class_number:
                                subcourse_data['classes'].append(class_number.get_text(strip=True))
                                mp4_url = get_mp4_url(class_url)
                                if mp4_url:
                                    subcourse_data['urls'].append(mp4_url)
                        
                        course_data['subcourses'].append(subcourse_data)
                        
                    except requests.RequestException as e:
                        print(f"Error processing subcourse {subcourse_url}: {e}")
                
                content_json.append(course_data)
                
            except requests.RequestException as e:
                print(f"Error processing course {course_url}: {e}")
                continue
        
        # Write to JSON file
        with open('openfing_content.json', 'w', encoding='utf-8') as f:
            json.dump(content_json, f, ensure_ascii=False, indent=2)
            
        return content_json
        
    except requests.RequestException as e:
        print(f"Error fetching main page: {e}")
        return [] 

def get_mp4_url(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Intentar encontrar <source src="...mp4">
        source_tag = soup.find("source", src=True)
        if source_tag:
            return source_tag["src"]

        # Si no hay <source>, intentar encontrar <iframe src="...youtube">
        iframe = soup.find("iframe", src=lambda x: x and "youtube" in x)
        if iframe:
            youtube_url = iframe.get("src")
            return youtube_url  
            # Podés retornar esto o manejarlo distinto
        print(f"No video found for {url}")
        return None
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

def get_video_size(url):
    try:
        head = requests.head(url, headers=HEADERS, allow_redirects=True)
        size_bytes = int(head.headers.get("Content-Length", 0))
        return size_bytes
    except Exception as e:
        print(f"Failed to get size for {url}: {e}")
        return 0

def format_size(bytes):
    return f"{bytes / (1024**3):.2f} GB"

def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    total_number_of_classes=0
    total_bytes = 0
    for course_key, value in data.items():
        classes = value.get("classes", [])
        for class_id in classes:
            mp4_url = get_mp4_url(course_key, class_id)
            if mp4_url:
                print(f"Processing: {mp4_url} from course:{course_key},class: {class_id}")
                size = get_video_size(mp4_url)
                total_bytes += size
                total_number_of_classes+=1
            else:
                print(f"No MP4 found for {course_key} - Class {class_id}")

    print("\n--- Summary ---")
    print(f"Total Size: {format_size(total_bytes)}")
    print(f"Numero Total de Clases: {total_number_of_classes}")

if __name__ == "__main__":
    #main()
    getCourseListContent()
