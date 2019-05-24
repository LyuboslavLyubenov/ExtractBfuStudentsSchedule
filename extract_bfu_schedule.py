import string
import requests
from bs4 import BeautifulSoup
import sys
import datetime


# Usage: BfuScheduleExtractor().extract_schedule(faculty, form, level)
class BfuScheduleExtractor(object):
    def get_select_tag_options_text(self, html_soup, id):
        options = html_soup.find(id=id).find_all('option')
        options = filter(lambda option: option['value'] != '0', options)
        return list(map(lambda option: option.text, options))

    def convert_url_to_soup(self, url):
        """Creates soup from response from GET request made to specified url"""
        request = requests.get(url)
        return BeautifulSoup(request.content, 'lxml')

    def get_schedules_urls(self, type, form, level):
        """Returns list containing links to all schedules (seperated by week) for specified major and year"""
        url = 'https://e-services.bfu.bg/common/graphic.php?c={}&o={}&k={}&submit=Покажи+графика'
        url = url.format(type, form, level)
        soup = self.convert_url_to_soup(url)
        schedule_a_tags = soup.find(id='info').find_all('a')
        return list(map(lambda tag: 'https://e-services.bfu.bg/common/' + tag.attrs['href'], schedule_a_tags))

    def extract_majors(self, majors_soup):
        """Extracts available majors from soup made from GET response made to any schedule page"""
        result = []
        majors_list = list(majors_soup)

        for i in range(0, len(majors_list)):
            major_element = majors_list[i]
            major_text = major_element.find('b').text.split()
            major = major_text[0].rstrip(string.digits)
            result.append(str(major) + ' група 1-' + str((i % 2) + 1))

        return result

    current_year = datetime.datetime.now().year

    def calculate_start_major_index(self, majors_schedule, from_time):
        major_index = 0

        for major_schedule in majors_schedule:
            if len(list(filter(lambda x: (x['from'] < from_time < x['to']), majors_schedule[major_schedule]))) == 0:
                break
            major_index += 1

        return major_index

    def extract_schedule_for_day(self, elements, majors):
        """ 
            Extracts schedule for day
            
            elements - html soup created from part of the table containing classes for one day
        """
        majors_schedule = {}

        for major in majors:
            majors_schedule[major] = []

        for element in elements:

            td_children = list(element.find_all('td'))
            date_and_time = td_children[0].text.split()[1:]
            date = list(map(lambda x: int(x), date_and_time[0].split('.')))
            start_time = int(date_and_time[1].split('-')[0])
            from_time = datetime.datetime(self.current_year, date[1], date[0], start_time)

            major_index = self.calculate_start_major_index(majors_schedule, from_time)

            for i in range(1, len(td_children)):

                if len(td_children[i].text.strip()) == 0:
                    major_index += 1
                    continue

                colspan = int(td_children[i].attrs['colspan'])

                for major_group_index in range(0, colspan):
                    major = majors[major_index]
                    rowspan = int(td_children[i].attrs['rowspan'])
                    to_time = datetime.datetime(self.current_year, date[1], date[0], start_time + rowspan)
                    majors_schedule[major].append(
                        {'from': from_time, 'to': to_time, 'course': ' '.join(list(td_children[i].strings))})
                    major_index += 1

        return majors_schedule

    def extract_schedule_from_url(self, url):
        soup = self.convert_url_to_soup(url)
        majors_soup = soup.find_all('th')[1:]
        majors = self.extract_majors(majors_soup)
        tr_elements = soup.find_all('tr')[1:]
        result = []

        for day_index in range(0, 7):
            day_elements = tr_elements[day_index * 12: (day_index * 12) + 12]
            result.append(self.extract_schedule_for_day(day_elements, majors))

        return result

    def extract_schedule(self, faculty, form, course_level):
        soup = self.convert_url_to_soup('https://e-services.bfu.bg/common/graphic.php')

        types = self.get_select_tag_options_text(soup, 'c')

        if faculty < 1 or faculty > len(types):
            sys.exit('Невалиден център на обучение')

        if form < 1 or form > 3:
            sys.exit('Невалидна форма на обучение')
            
        #form with id 3 have to complete 6 semesters :(
        available_course_levels = range(1, 6 if form != 3 else 3)
        available_course_levels = list(map(lambda level: str(level), available_course_levels))
        
        if str(course_level) not in available_course_levels:
            sys.exit('Невалиден курс')
        
        schedules_urls = self.get_schedules_urls(faculty, form, course_level)[::-1]
        schedule = []

        for url in schedules_urls:
            schedule += self.extract_schedule_from_url(url)

        return schedule
