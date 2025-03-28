#The script is a simple GUI application that allows you to enter your LinkedIn credentials, job title, location, job type, job level, and whether you want to filter for easy apply jobs. When you click the “Start Scraping” button, the script will open a Chrome browser, log in to LinkedIn, and scrape jobs based
import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import csv
import json

def save_credentials():
    credentials = {
        "email": email_entry.get(),
        "password": password_entry.get(),
        "remember": remember_var.get()
    }
    with open("credentials.json", "w") as file:
        json.dump(credentials, file)

def load_credentials():
    try:
        with open("credentials.json", "r") as file:
            credentials = json.load(file)
            email_entry.insert(0, credentials.get("email", ""))
            password_entry.insert(0, credentials.get("password", ""))
            remember_var.set(credentials.get("remember", False))
    except FileNotFoundError:
        pass

def start_scraping():
    job_title = job_entry.get()
    location = location_entry.get()
    email = email_entry.get()
    password = password_entry.get()
    job_type = job_type_var.get()
    job_level = job_level_var.get()
    easy_apply = easy_apply_var.get()

    if not job_title or not email or not password:
        messagebox.showerror("Input Error", "Please enter job title, email, and password.")
        return

    if remember_var.get():
        save_credentials()

    messagebox.showinfo("Process Started", "The job scraping process has started. Please wait...")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    total_jobs = 0

    try:
        with open('linkedin_jobs.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header if file is empty
            if file.tell() == 0:
                writer.writerow(["Title", "Company", "Location", "Link"])

            # Log in to LinkedIn
            driver.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(3, 6))
            driver.find_element(By.ID, "username").send_keys(email)
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(random.uniform(3, 6))

            # Build the search URL with filters
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
            if job_type:
                search_url += f"&f_WT={job_type}"
            if job_level:
                search_url += f"&f_E={job_level}"
            if easy_apply:
                search_url += "&f_AL=true"

            driver.get(search_url)
            time.sleep(random.uniform(3, 6))

            # Extract the subtitle value before scraping
            try:
                subtitle_element = driver.find_element(By.CLASS_NAME, "jobs-search-results-list__subtitle")
                subtitle_value = subtitle_element.text
            except Exception as e:
                subtitle_value = "Unable to find subtitle"
                print(f"Error fetching subtitle: {e}")

            # Show confirmation message box with subtitle value
            response = messagebox.askyesno("Confirm Filters", f"Found subtitle: {subtitle_value}\nDo you want to continue with scraping?")
            if not response:
                messagebox.showinfo("Process Cancelled", "Please modify the filter and try again.")
                driver.quit()
                return

            def scrape_jobs():
                job_list = []
                try:
                    job_elements = WebDriverWait(driver, 15).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "xClRpgOKBlCsqFqUKXZPdCcYXYbSQ"))
                    )
                except Exception as e:
                    print("Job elements not found:", e)
                    return job_list

                for job in job_elements:
                    try:
                        title = job.find_element(By.CLASS_NAME, "ryrLncXWuPIaGVYycuYCzNYRICvlvZmbrjZvw").text
                        company = job.find_element(By.CLASS_NAME, "JYOiFvKUCfOKQdhEEMNkiIVoqrjgTIZOFwhJmM").text
                        location_text = job.find_element(By.CLASS_NAME, "thziVonUUlrcARJcxqJqBlflUGRrQeCsNxg").text
                        link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
                        job_list.append([title, company, location_text, link])
                    except Exception as e:
                        print("Error extracting job details:", e)
                        continue
                return job_list

            page = 1
            while True:
                print(f"Scraping page {page}...")
                job_list = scrape_jobs()
                if job_list:
                    for job in job_list:
                        writer.writerow(job)
                    total_jobs += len(job_list)
                    print(f"✅ Scraped {len(job_list)} jobs from page {page}.")
                else:
                    print("No jobs found on this page.")

                time.sleep(random.uniform(3, 6))

                try:
                    active_page_li = driver.find_element(By.XPATH, "//li[contains(@class, 'artdeco-pagination__indicator--number') and contains(@class, 'active')]")
                    next_li = active_page_li.find_element(By.XPATH, "following-sibling::li[1]")
                    next_text = next_li.text.strip()

                    if next_text == "…":
                        print("Encountered ellipsis, clicking to reveal more pages...")
                        next_li.click()
                        time.sleep(random.uniform(3, 6))
                        continue

                    print(f"Navigating to page {next_text}...")
                    next_button = next_li.find_element(By.TAG_NAME, "button")
                    next_button.click()
                    time.sleep(random.uniform(3, 6))
                    page = int(next_text)
                except Exception as e:
                    print("No further pages available or error encountered:", e)
                    break

        messagebox.showinfo("Process Completed", f"Scraping finished. {total_jobs} jobs saved to linkedin_jobs.csv")
    finally:
        driver.quit()

root = tk.Tk()
root.title("LinkedIn Job Scraper")
root.geometry("450x500")
root.configure(bg="#f0f0f0")

tk.Label(root, text="Email:", bg="#f0f0f0").pack(pady=5)
email_entry = tk.Entry(root, width=40)
email_entry.pack(pady=5)

tk.Label(root, text="Password:", bg="#f0f0f0").pack(pady=5)
password_entry = tk.Entry(root, width=40, show="*")
password_entry.pack(pady=5)

remember_var = tk.BooleanVar()
tk.Checkbutton(root, text="Remember Me", variable=remember_var, bg="#f0f0f0").pack(pady=5)

tk.Label(root, text="Job Title:", bg="#f0f0f0").pack(pady=5)
job_entry = tk.Entry(root, width=40)
job_entry.pack(pady=5)

tk.Label(root, text="Location:", bg="#f0f0f0").pack(pady=5)
location_entry = tk.Entry(root, width=40)
location_entry.pack(pady=5)

tk.Label(root, text="Job Type (Onsite(1)/Remote(2)/Hybrid(3)):", bg="#f0f0f0").pack(pady=5)
job_type_var = tk.StringVar()
tk.Entry(root, textvariable=job_type_var, width=40).pack(pady=5)

tk.Label(root, text="Job Level (Internship(1)/Entry(2)/Associate(3)/Mid(4)/Senior(5)):", bg="#f0f0f0").pack(pady=5)
job_level_var = tk.StringVar()
tk.Entry(root, textvariable=job_level_var, width=40).pack(pady=5)

easy_apply_var = tk.BooleanVar()
tk.Checkbutton(root, text="Easy Apply Only", variable=easy_apply_var, bg="#f0f0f0").pack(pady=5)

tk.Button(root, text="Start Scraping", command=start_scraping, bg="#0073b1", fg="white").pack(pady=20)

load_credentials()
root.mainloop()
    
    