#!/usr/bin/env python
from subprocess import Popen, call, PIPE
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import urllib3

ENV_PATH = "/home/watermellon/Workplace/go-environment/"
MAGENTO_PATH = "/home/watermellon/Workplace/magento/"
EXECUTE_PATH = "/tmp/uat/"
EXECUTE_SRC = "/tmp/uat/src/"
PKG_PATH = "/tmp/product-packages/"


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
	call(["tar", "xvf", packages[0], "-C", PKG_PATH], cwd=PKG_PATH)
	print("> Unzip package successfully")
	os.chdir(PKG_PATH)
	call(["npm", "install", "--prefix", PKG_PATH + packages[0].split(".tar.gz")[0] + "/client/pos"])
	call(["npm", "run-script", "build", "--prefix", PKG_PATH + packages[0].split(".tar.gz")[0] + "/client/pos"])
	call(["mkdir", "-p", 
		PKG_PATH + packages[0].split(".tar.gz")[0] + "/server/app/code/Magestore/Webpos/build/apps"
		])
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
			
			call(["cp", "-r", "app", EXECUTE_SRC + "app"])
			call(["cp", "-r", "magmi", EXECUTE_SRC])
			call(["cp", "-r", "pub", EXECUTE_SRC + "pub"])
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento setup:upgrade")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento setup:di:compile")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento set:static-content:deploy -f")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento indexer:reindex")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento webpos:deploy")
			os.system("docker exec -u www-data -i uat_web_1 php bin/magento cache:flush")


# Running each instances
# - Copy Magento source to appropriate folder
# - Change folder permission and clean up
# - Start the container
def up_instance():
	magento_list = get_magento()
	env_list = get_env()
	for magento_version in magento_list:
		for env in env_list:
			if magento_version != "2.3.0" and "PHP7.2" not in env:
				# Prepare the folder structure
				proc = Popen(["mkdir", "-p", EXECUTE_SRC], stdin=PIPE)
				print("> Create folder done")
				proc = Popen(["sudo", "chown", "-R", "1000:1000", EXECUTE_PATH])
			
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
				
				status_front = False
				status_pos = False
				if check_front():
					status_front = True
				if check_pos():
					status_pos = True
				
				terminate_instance()
				part_env = env.split("/")
				
				with open("result.log", "a+") as res_writer:
					res.writer.write(env[len(part_env-1)] + "\n")
					if status_front:
						res.writer.write("Front: PASS\n")
					else:
						res.writer.write("Front: FAILED\n")
					if status_pos:
						res.writer.write("POS: PASS\n")
					else:
						res.writer.write("POS: FAILED\n")
				break
				
		break


# Test front page
def check_front():
	status = False
	# Check front status
	http = urllib3.PoolManager()
	res = http.request("GET", "http://localhost:9100")
	if res.status == 200:
		status = True
	else:
		status = False
		
	# Check admin page
	res = http.request("GET", "http://localhost:9100/admin")
	if res.status == 200:
		status = True
	else:
		status = False
		

# Test login page
def check_pos():
	status = False
	http = urllib3.PoolManager()
	res = http.request("GET", "http://localhost:9100/apps/pos/index.html#/login")
	if res.status == 200:
		status = True
	else:
		status = False


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
	up_instance()
	
	
if __name__ == "__main__":
	main()
