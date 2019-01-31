#!/usr/bin/env python
from subprocess import Popen, call, PIPE
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

ENV_PATH = "/home/watermellon/Workplace/go-environment/"
MAGENTO_PATH = "/home/watermellon/Workplace/magento/"
EXECUTE_PATH = "/tmp/uat/"
EXECUTE_SRC = "/tmp/uat/src/"
PKG_PATH = "/tmp/product-packages/"
SUDO = "water123@"
FIRST_RUN_FLAG = False


# Listing all folder Apache
def get_env():
	env_list = os.listdir(ENV_PATH)
	if env_list:
		# Get all folder in here
		return [ENV_PATH + env for env in env_list]


# Listing all Magento source folder
def get_magento():
	magento_list = os.listdir(MAGENTO_PATH)
	if magento_list:
		return [ver.split("_")[0] for ver in magento_list]
		
		
def prepare_package():
	packages = os.listdir(PKG_PATH)
	if not FIRST_RUN_FLAG:
		call(["tar", "xvf", packages[0], "-C", PKG_PATH], cwd=PKG_PATH)
		print("> Unzip package successfully")
		os.chdir(PKG_PATH)
		call(["npm", "install", "--prefix", PKG_PATH + packages[0].split(".tar.gz")[0] + "/client/pos"])
		call(["npm", "run-script", "build", "--prefix", PKG_PATH + packages[0].split(".tar.gz")[0] + "/client/pos"])
		call(["mkdir", "-p", 
			PKG_PATH + packages[0].split(".tar.gz")[0] + "/server/app/code/Magestore/Webpos/build/apps"
			])
		FIRST_RUN_FLAG = True
	if FIRST_RUN_FLAG:
		call(["cp", 
			"-Rf", 
			PKG_PATH + packages[0].split(".tar.gz")[0] + "/client/pos/build",
			PKG_PATH + packages[0].split(".tar.gz")[0] + "/server/app/code/Magestore/Webpos/build/apps/pos"
		])
		
		
def install_package():
	packages = os.listdir(PKG_PATH)
	for folder in packages:
		if "tar.gz" not in folder:
			os.chdir(PKG_PATH + folder + "/server")
			
			call(["cp", "-r", "app", EXECUTE_SRC])
			call(["cp", "-r", "magmi", EXECUTE_SRC])
			call(["cp", "-r", "pub", EXECUTE_SRC])
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento setup:upgrade")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento setup:di:compile")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento set:static-content:deploy -f")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento indexer:reindex")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento webpos:deploy")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento cache:flush")
			
			
def process_instance(magento_version, env):
	# Prepare the folder structure
	proc = Popen(["mkdir", "-p", EXECUTE_SRC], stdin=PIPE)
	print("> Create folder done")
	proc = Popen(["sudo", "chown", "-R", "1000:1000", EXECUTE_PATH])
	proc.communicate(bytes(SUDO, 'utf-8'))

	# Copy Magento source
	call([
		"tar", 
		"xvf", 
		"{0}_sample_data.tar.gz".format(magento_version), 
		"-C",
		EXECUTE_SRC], cwd=MAGENTO_PATH)
	
	proc = Popen(["sudo", "chmod", "+x", "{0}bin/magento".format(EXECUTE_SRC)])
	print("> Unzip & set permission done")

	# Copy env file
	call(["cp", "docker-compose.yml", EXECUTE_PATH], cwd=env)
	call(["cp", "env", EXECUTE_PATH], cwd=env)
	print("> Copy configuration done")

	# Change permission
	call(["sudo", "chown", "-R", "1000:1000", EXECUTE_SRC])

	# Bring everthing up
	call(["docker-compose", "up", "-d"], cwd=EXECUTE_PATH)
	time.sleep(60)
	
	os.system("docker update --cpus='1.5' uat_web_1")				
	
	# Install Magento
	os.system("docker exec -i uat_web_1 install-magento")
	
	# Prepare package
	prepare_package()
	install_package()
	
	# Check
	flag = True
	env_part = env.split("/")
	result = test_uat(magento_version, env_part[len(env_part) - 1])
	for res in result:
		if not res:
			flag = False
			break
	with open("/tmp/result.log", "a+") as result_writer:
		if flag:
			result_writer.write(env_part[len(env_part) - 1] + " " + magento_version + " - PASSED\n")
		if not flag:
			result_writer.write(env_part[len(env_part) - 1] + " " + magento_version + " - FAILED\n")
	
	# Terminate
	# terminate_instance()


# Running each instances
# - Copy Magento source to appropriate folder
# - Change folder permission and clean up
# - Start the container
def up_instance(version):
	magento_list = get_magento()
	env_list = get_env()
	
	for magento_version in magento_list:
		for env in env_list:
			if version == "2.2":
				if magento_version != "2.3.0" and "PHP7.2" not in env:
					process_instance(magento_version, env)
					
			if version == "2.3":
				if magento_version == "2.3.0" and "PHP7.2" in env:
					process_instance(magento_version, env)
		
		
# Test front page
def test_uat(version, env):
	test_front_normal = False
	test_front_admin = False
	test_pos = False
	
	driver = webdriver.Firefox()

	try:
		driver.get("http://localhost:9100")
		element_check = WebDriverWait(driver, 30).until(
			EC.presence_of_element_located((By.CLASS_NAME, 'product-image-photo'))
		)
		if element_check:
			test_front_normal = True
			driver.get("http://localhost:9100/admin")
			element_check = WebDriverWait(driver, 30).until(
				EC.presence_of_element_located((By.CLASS_NAME, 'admin__field-control'))
			)
			if element_check:
				test_front_admin = True
			else:
				test_front_admin = False
		else:
			test_front_normal = False
		
		'''	
		if version == "2.3":
			driver.get("http://localhost:9100/pub/apps/pos/#/login")
		if version == "2.2":
			driver.get("http://localhost:9100/apps/pos/index.html#/login")
		'''	
		driver.get("http://localhost:9100/pub/apps/pos/#/login")
		
		element_check = WebDriverWait(driver, 30).until(
			EC.presence_of_element_located((By.ID, 'username'))
		)
		if element_check:
			test_pos = True
		else:
			test_pos = False
	except:
		print("Error")
		driver.save_screenshot("/tmp/{0}.png".format(env))
		
	os.system("pkill firefox")
	os.system("pkill geckodriver")
	
	return test_front_normal, test_front_admin, test_pos


# Terminate instance
def terminate_instance():
	call(["docker-compose", "down"], cwd=EXECUTE_PATH)
	call(["docker", "volume", "prune", "-f"])
	call(["rm", "-rf", EXECUTE_PATH])
	packages = os.listdir(PKG_PATH)
	for folder in packages:
		if "tar.gz" not in folder:
			call(["rm", "-rf", PKG_PATH + folder])
	print("> Clean is clear")


def main():
	up_instance(version="2.2")
	
	
if __name__ == "__main__":
	main()
