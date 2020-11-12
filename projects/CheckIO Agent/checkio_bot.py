import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import sys
import time


def read_credentials():
    secrets = 'secrets.json'
    with open(secrets) as file:
        keys = json.loads(file.read())
        return keys

@dataclass
class Task:
    name: str
    link: str

class checkioSolver:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.google = 'https://www.google.com/'
        self.base_url = 'https://checkio.org'
        self.SEARCH_TEXT= "Python CheckIO "
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.command_or_control = Keys.COMMAND if sys.platform == 'darwin' else Keys.CONTROL

    def multiple_run(self):
        for i in range(10):
            # every iteration may give you new islands and tasks unlocked
            self.single_iteration_over_session()
            print("Single iteration #: ", i)

    def single_iteration_over_session(self):
        self.login_to_checkio()
        time.sleep(10)
        links = self.get_islands_links()
        self.iterate_over_islands_and_solve_tasks(links)
        print(links)
        time.sleep(5)
        self.driver.quit()

    def iterate_over_islands_and_solve_tasks(self, links_to_islands):
        for island in links_to_islands:
            unsolved_island_tasks = self.get_unsolved_tasks_from_island(island)
            amount_of_unsolved_tasks = len(unsolved_island_tasks)
            if amount_of_unsolved_tasks:
                print("Tasks to solve: ", amount_of_unsolved_tasks)
                self.solve_tasks_on_island(unsolved_island_tasks)
            else:
                print("No tasks to solve on ", island)
            time.sleep(5)

    def solve_tasks_on_island(self, task_to_solve):
        for task in task_to_solve:
            if self.solve_one_task(task):
                print(task.name, ' SOLVED!! WUU YAYY **')
            else:
                print(task.name, " Can't be solved SAD ;(")

    def solve_one_task(self, task):
        print("Solving current task: ", task.name)
        solution_links = self.get_google_solutions_for_task(task)
        task_solved = False
        for solution in solution_links:
            solution_code = self.copy_solution(solution)
            if solution_code and self.solve_and_check_task(solution_code, task):
                task_solved = True
                break
        return task_solved

    def solve_and_check_task(self, solution_code, task):
        self.driver.get(f'{self.base_url}{task.link}')
        time.sleep(10)
        try:
            self.driver.find_element_by_xpath("//a[@class='btn']").click()
        except ElementClickInterceptedException:
            self.driver.find_element_by_xpath(
                "//div[@class='congratulation__body__accept']").click()
            time.sleep(4)
            self.driver.find_element_by_xpath("//a[@class='btn']").click()
        time.sleep(4)
        solution_textarea = self.driver.find_element_by_xpath('//textarea')
        solution_textarea.send_keys(self.command_or_control +'a')
        solution_textarea.send_keys(Keys.DELETE)
        for line in solution_code:
            solution_textarea.send_keys(line)
            solution_textarea.send_keys('\n')
            solution_textarea.send_keys(Keys.HOME)
        time.sleep(5)
        self.driver.find_element_by_id('check-code-btnInnerEl').click()
        time.sleep(5)
        print("Task is being checked... hold on!")
        for current_attempt in range(20):
            try:
                succesed_element = self.driver.find_element_by_xpath("//div[@class='animation-success']")
                time.sleep(2)
                if succesed_element:
                    print("Completed task: " + task.name)
                    return True
                time.sleep(5)

            except NoSuchElementException:
                print("Element //div[@class='animation-success'] cannot be found")

            print("Attemp #: ", current_attempt)
        print("Failed Task: ", task.name)
        return False

    def copy_solution(self, solution_link):
        self.driver.get(solution_link)
        time.sleep(3)
        try:
            publications_code = self.driver.find_element_by_xpath(
                "//div[@class='publications__info__code']")
            solution_code = publications_code.find_elements_by_xpath(
                "//span[@style='padding-right: 0.1px;']")
            curr_google_solution_code = []
            for data in solution_code:
                code_words = data.find_elements_by_css_selector('span')
                code_line = ""
                for word in code_words:
                    code_line += word.text
                if len(code_line) > 0:
                    curr_google_solution_code.append(code_line)
            return curr_google_solution_code
        except Exception as e:
            print(e)
            print('Cant get solution from: ', solution_link)
            return ''

    def get_google_solutions_for_task(self, task):
        print("Google Search: " + task.name + "\n")
        self.driver.get(self.google)
        time.sleep(2)
        searchbox = self.driver.find_element_by_name("q")
        searchbox.send_keys(self.SEARCH_TEXT + task.name)
        time.sleep(1)
        searchbox.submit()
        time.sleep(8)
        google_results = self.driver.find_elements_by_xpath(
            "//div[@class='yuRUbf']/a[contains(@href,'publications')]")
        time.sleep(3)
        current_google_result_links = []
        for results in google_results:
            current_google_result_links.append(results.get_attribute("href"))
        time.sleep(3)
        return current_google_result_links

    def get_unsolved_tasks_from_island(self, link_to_island):
        self.driver.get(link_to_island)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        tasks =  soup.find_all(class_='island-tasks__container')
        unsolved_tasks = []
        for task in tasks:
            try:
                task_status =  task.find(class_='island-tasks__side__sign').get('title')
                if task_status != 'Solved' and task_status != 'Blocked':
                    title = task.find(class_='island-tasks__task__title').get('title')
                    link = task.find('a').get('href')
                    unsolved_tasks.append(Task(title, link))
            except Exception as e:
                print(e)
        return unsolved_tasks

    def get_islands_links(self):
        opened_stations = self.driver.find_elements_by_xpath(
            "//div[contains(@class,'map__station_state_opened')]")
        opened_stations_links = []
        for link in opened_stations:
            opened_stations_links.append(
                link.find_element_by_css_selector('a.map__station__link').get_attribute("href"))
        print(opened_stations_links)
        return opened_stations_links

    def login_to_checkio(self):
        self.driver.get(self.base_url)
        self.get_on_python_checkio()
        self.put_credentials_to_form()

    def get_on_python_checkio(self):
        try:
            self.driver.find_element_by_link_text('Python').click()
            time.sleep(5)
        except NoSuchElementException:
            print("***Incorrect Page...")

    def put_credentials_to_form(self):
        try:
            self.driver.find_element_by_id('id_username').send_keys(self.login)
            time.sleep(3)
            password_field = self.driver.find_element_by_id('id_password')
            password_field.send_keys(self.password)
            password_field.submit()
            time.sleep(3)
        except NoSuchElementException:
            print("FAILED login to checkio python")

#Main run
if __name__ == '__main__':
    credentials = read_credentials()
    bot = checkioSolver(credentials.get('username'), credentials.get('password'))
    bot.multiple_run()
    #bot.single_iteration_over_session()
    #bot.get_google_solutions_for_task(Task("First Word (simplified)", "https://py.checkio.org/en/mission/first-word-simplified/"))
     
