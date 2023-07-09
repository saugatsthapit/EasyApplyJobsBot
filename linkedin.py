import time,math,random,os
import utils,constants,config

from selenium import webdriver
from selenium.webdriver.common.by import By
from utils import prRed,prYellow,prGreen
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

class Linkedin:
    def __init__(self):
            prYellow("🌐 Bot will run in Chrome browser and log in Linkedin for you.")
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=utils.chromeBrowserOptions())
            self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            self.recordList = {
                'selectBox':{
                    'disability': 2,
                    'veteran': 3,
                    'race': 'Asian',
                    'gender': 'Male',
                    'sponsor': 1,
                    'authorized': 'Yes'
                },
                'comboBox':{
                    'city': 'Philadelphia, Pennsylvania, United States',
                },
                'textBox':{
                    'hear': 'LinkedIn',
                    'city': 'Philadelphia',
                    'state': 'Pennsylvania',
                    'salary': '120000',
                    'years': '8'
                },
                'radio':{
                    'authorized': 'Yes',
                    'sponsor': 'No',
                    'citizen': 'Yes'
                }
            }
            self.recordList = json.dumps(self.recordList)
            self.recordList= json.loads(self.recordList)
            prYellow("🔄 Trying to log in linkedin...")
            try:    
                self.driver.find_element("id","username").send_keys(config.email)
                time.sleep(2)
                self.driver.find_element("id","password").send_keys(config.password)
                time.sleep(2)
                self.driver.find_element("xpath",'//button[@type="submit"]').click()
                time.sleep(5)
                self.mongoConnection("Check")
            except:
                prRed("❌ Couldn't log in Linkedin by using Chrome. Please check your Linkedin credentials on config files line 7 and 8. If error continue you can define Chrome profile or run the bot on Firefox")


    
    def generateUrls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try: 
            with open('data/urlData.txt', 'w',encoding="utf-8" ) as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url+ "\n")
            prGreen("✅ Urls are created successfully, now the bot will visit those urls.")
        except:
            prRed("❌ Couldn't generate url, make sure you have /data folder and modified config.py file for your preferances.")

    def linkJobApply(self):
        self.generateUrls()
        countApplied = 0
        countJobs = 0

        urlData = utils.getUrlDataFile()

        for url in urlData:        
            self.driver.get(url)

            totalJobs = self.driver.find_element(By.XPATH,'//small').text 
            totalPages = utils.jobsToPages(totalJobs)

            urlWords =  utils.urlToKeywords(url)
            lineToWrite = "\n Category: " + urlWords[0] + ", Location: " +urlWords[1] + ", Applying " +str(totalJobs)+ " jobs."
            self.displayWriteResults(lineToWrite)

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url +"&start="+ str(currentPageJobs)
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))

                offersPerPage = self.driver.find_elements(By.XPATH,'//li[@data-occludable-job-id]')
                offerIds = []

                time.sleep(random.uniform(1, constants.botSpeed))

                for offer in offersPerPage:
                    offerId = offer.get_attribute("data-occludable-job-id")
                    offerIds.append(int(offerId.split(":")[-1]))

                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1

                    jobProperties = self.getJobProperties(countJobs)
                    if "blacklisted" in jobProperties: 
                        lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " +str(offerPage)
                        self.displayWriteResults(lineToWrite)
                    
                    else :                    
                        button = self.easyApplyButton()

                        if button is not False:
                            button.click()
                            time.sleep(random.uniform(1, constants.botSpeed))
                            countApplied += 1
                            try:
                                self.chooseResume()
                                self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
                                time.sleep(random.uniform(1, constants.botSpeed))

                                lineToWrite = jobProperties + " | " + "* 🥳 Just Applied to this job: "  +str(offerPage)
                                self.displayWriteResults(lineToWrite)

                            except:
                                try:
                                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Continue to next step']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))

                                    comPercentage = self.driver.find_element(By.XPATH,'html/body/div[3]/div/div/div[2]/div/div/span').text
                                    percenNumber = int(comPercentage[0:comPercentage.index("%")])
                                    result = self.applyProcess(percenNumber,offerPage)
                                    lineToWrite = jobProperties + " | " + result
                                    self.displayWriteResults(lineToWrite)
                                
                                except Exception as e: 
                                    self.chooseResume()
                                    lineToWrite = jobProperties + " | " + "* 🥵 Cannot apply to this Job! " +str(offerPage)
                                    self.displayWriteResults(lineToWrite)
                        else:
                            lineToWrite = jobProperties + " | " + "* 🥳 Already applied! Job: " +str(offerPage)
                            self.displayWriteResults(lineToWrite)


            prYellow("Category: " + urlWords[0] + "," +urlWords[1]+ " applied: " + str(countApplied) +
                  " jobs out of " + str(countJobs) + ".")
        
        utils.donate(self)

    def chooseResume(self):
        try: 
            beSureIncludeResumeTxt = self.driver.find_element(By.CLASS_NAME, "jobs-document-upload__title--is-required")
            if(beSureIncludeResumeTxt.text == "Be sure to include an updated resume"):
                resumes = self.driver.find_elements(By.CSS_SELECTOR,"button[aria-label='Choose Resume']")
                if(len(resumes) == 1):
                    resumes[0].click()
                elif(len(resumes)>1):
                    resumes[config.preferredCv-1].click()
                else:
                    prRed("❌ No resume has been selected please add at least one resume to your Linkedin account.")
        except:
            pass

    def getJobProperties(self, count):
        textToWrite = ""
        jobTitle = ""
        jobCompany = ""
        jobLocation = ""
        jobWOrkPlace = ""
        jobPostedDate = ""
        jobApplications = ""

        try:
            jobTitle = self.driver.find_element(By.XPATH,"//h1[contains(@class, 'job-title')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blackListTitles if(blItem.lower() in jobTitle.lower())]
            if (len(res)>0):
                jobTitle += "(blacklisted title: "+ ' '.join(res)+ ")"
        except Exception as e:
            if(config.displayWarnings):
                prYellow("⚠️ Warning in getting jobTitle: " +str(e)[0:50])
            jobTitle = ""

        try:
            jobCompany = self.driver.find_element(By.XPATH,"//a[contains(@class, 'ember-view t-black t-normal')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blacklistCompanies if(blItem.lower() in jobTitle.lower())]
            if (len(res)>0):
                jobCompany += "(blacklisted company: "+ ' '.join(res)+ ")"
        except Exception as e:
            if(config.displayWarnings):
                prYellow("⚠️ Warning in getting jobCompany: " +str(e)[0:50])
            jobCompany = ""
            
        try:
            jobLocation = self.driver.find_element(By.XPATH,"//span[contains(@class, 'bullet')]").get_attribute("innerHTML").strip()
        except Exception as e:
            if(config.displayWarnings):
                prYellow("⚠️ Warning in getting jobLocation: " +str(e)[0:50])
            jobLocation = ""

        try:
            jobWOrkPlace = self.driver.find_element(By.XPATH,"//span[contains(@class, 'workplace-type')]").get_attribute("innerHTML").strip()
        except Exception as e:
            if(config.displayWarnings):
                prYellow("⚠️ Warning in getting jobWorkPlace: " +str(e)[0:50])
            jobWOrkPlace = ""

        try:
            jobPostedDate = self.driver.find_element(By.XPATH,"//span[contains(@class, 'posted-date')]").get_attribute("innerHTML").strip()
        except Exception as e:
            if(config.displayWarnings):
                prYellow("⚠️ Warning in getting jobPostedDate: " +str(e)[0:50])
            jobPostedDate = ""

        try:
            jobApplications= self.driver.find_element(By.XPATH,"//span[contains(@class, 'applicant-count')]").get_attribute("innerHTML").strip()
        except Exception as e:
            if(config.displayWarnings):
                prYellow("⚠️ Warning in getting jobApplications: " +str(e)[0:50])
            jobApplications = ""

        textToWrite = str(count)+ " | " +jobTitle+  " | " +jobCompany+  " | "  +jobLocation+ " | "  +jobWOrkPlace+ " | " +jobPostedDate+ " | " +jobApplications
        return textToWrite

    def easyApplyButton(self):
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            button = self.driver.find_element(By.XPATH,
                '//button[contains(@class, "jobs-apply-button")]')
            EasyApplyButton = button
        except: 
            EasyApplyButton = False

        return EasyApplyButton

    def checkOptionType(self, group):
        try:
            radio = group.find_elements(By.XPATH, "div//input[contains(@type, 'radio')]") #checks for radio button
            if len(radio)>0:
                return ['radio',radio]
            else:
                raise Exception
        except:
            try:
                txtBox = group.find_element(By.XPATH, "div//input[contains(@type, 'text')]")
                if txtBox.aria_role == 'combobox':
                    return ['comboBox',txtBox]
                elif txtBox.aria_role == 'textbox':
                    return ['textBox',txtBox]
                else:
                    raise Exception
            except:
                try:
                    selectBox=group.find_element(By.XPATH, "div//select[starts-with(@id, 'text-entity-list-form')]") #select
                    selectBox = Select(selectBox)
                    return ['selectBox',selectBox]
                except:
                    print('None of the optionType')

    def applyProcess(self, percentage, offerPage):
        applyPages = math.floor(100 / percentage) 
        result = ""  
        try:
            for pages in range(applyPages-1):
                groupList= self.driver.find_elements(By.XPATH, "//div[contains(@class, 'jobs-easy-apply-form-section__grouping')]")
                for group in groupList:
                    questionText = group.text.lower()
                    optionType = self.checkOptionType(group)
                    if optionType[0] == 'selectBox':
                        record= 0
                        for key in self.recordList[optionType[0]]:
                            if key in questionText:
                                record=key
                                value= self.recordList[optionType[0]][key]
                                if type(value) is int:
                                    optionType[1].select_by_index(value)
                                else:
                                    optionType[1].select_by_value(value)
                            else:
                                continue
                    elif optionType[0] == 'textBox' or optionType[0]=='comboBox':
                        for key in self.recordList[optionType[0]]:
                            value= self.recordList[optionType[0]][key]
                            if optionType[0] is not 'comboBox':
                                if key in questionText:
                                    optionType[1].clear()
                                    optionType[1].send_keys(value)
                                else:
                                    continue
                            else:
                                if key in questionText:
                                    optionType[1].clear()
                                    optionType[1].send_keys(value)
                                    optionType[1].send_keys(Keys.ARROW_DOWN)
                                    optionType[1].send_keys(Keys.ENTER)
                                else:
                                    continue

                    elif optionType[0] == 'radio':
                        for key in self.recordList[optionType[0]]:
                            value= self.recordList[optionType[0]][key]
                            if key in questionText:
                                group.find_element(By.XPATH, "div//label[contains(@data-test-text-selectable-option__label, "+str(value)+")]").click()
                            else:
                                group.find_element(By.XPATH, "div//label[contains(@data-test-text-selectable-option__label, 'Yes')]").click()
                    elif 'acknowledge' in questionText:
                        group.find_element(By.XPATH, "div//label").click()
                try:    
                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Continue to next step']").click()
                    time.sleep(random.uniform(1, constants.botSpeed))
                except:
                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Review your application']").click() 
                    time.sleep(random.uniform(1, constants.botSpeed))

            if config.followCompanies is False:
                self.driver.find_element(By.CSS_SELECTOR,"label[for='follow-company-checkbox']").click() 
                time.sleep(random.uniform(1, constants.botSpeed))

            self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Submit application']").click()
            time.sleep(random.uniform(1, constants.botSpeed))

            result = "* 🥳 Just Applied to this job: " +str(offerPage)
        except:
            # PRO FEATURE! OUTPUT UNANSWERED QUESTIONS, APPLY THEM VIA OPENAI, output them.
            result = "* 🥵 " +str(applyPages)+ " Pages, couldn't apply to this job! Extra info needed. Link: " +str(offerPage)
        return result

    def displayWriteResults(self,lineToWrite: str):
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            prRed("❌ Error in DisplayWriteResults: " +str(e))

start = time.time()
Linkedin().linkJobApply()
end = time.time()
prYellow("---Took: " + str(round((time.time() - start)/60)) + " minute(s).")
