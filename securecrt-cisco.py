# $language = "python"
# $interface = "1.0"

################################################################################
####	Created by: Cubog													####
####	Date: 1/13/16														####
####	Edited: 1/26/16													####
####	Based on scripts provided by VanDyke Software						####
####	https://www.vandyke.com/support/securecrt/python_examples.html		####
################################################################################

# Connect to an device using SSH2 protocol. Specify the  username and password 
# in the variables. Get the hostname from a file called hosts.txt located
# in the same folder. It will get the vlans from each  port and add a voice vlan


import os
import sys
import re
import time


user = ""
passwd = ""



def get_prompt():
	# Reads the line the cursor is located at and extracts the prompt
	row = crt.Screen.CurrentRow
	prompt = crt.Screen.Get(row, 0, row, crt.Screen.CurrentColumn - 1)
	prompt = prompt.strip()
	return prompt
	
def main():
	# Open the file with the hosts
	file = open("hosts.txt", "rb")
	
	# Create array to hold the hostnames
	sessionsArray = []
	
	# Loop thru the file and get the hostname from each line
	# Add each hostname to the array
	for line in file:
		session = line.strip()
		if session:	# Don't add empty lines/sessions
			sessionsArray.append(session)
	# Close the file
	file.close()
	
	# Loop thru the list of hosts and run program
	for session in sessionsArray:
		# Lists for ports and vlans
		portArray = []
		vlanArray = []
		voiceArray = []
		#save the hostname into variable host
		fqdn = session
		
		# Added this code to save config to tftp server
		#hostArray = fqdn.split(".")
		#host = hostArray[0]
		# Add time stamp to save to tftp
		#host += "_" + time.strftime("%H-%M-%S")
		
		# Prompt for a password instead of embedding it in a script...
		#passwd = crt.Dialog.Prompt("Enter password for " + host, "Login", "", True)
		
		# Build a command-line string to pass to the Connect method.
		cmd = "/SSH2 /ACCEPTHOSTKEYS /L %s /PASSWORD %s /C 3DES /M MD5 %s" % (user, passwd, fqdn)
		crt.Session.Connect(cmd)
		
		tab = crt.GetScriptTab()
		# Check to see if it is connected
		# If not connected provide error
		if tab.Session.Connected != True:
			crt.Dialog.MessageBox(
				"Error.\n" +
				"This script was designed to be launched after a valid "+
				"connection is established.\n\n"+
				"Please connect to a remote machine before running this script.")
			return
			
		# If connected start the program
		if tab.Session.Connected:
				crt.Screen.Synchronous = True
				
				# Open a file for writing.
				filename = os.path.join(os.environ['TEMP'], 'output.txt')
				fp = open(filename, "wb+")

				# When we first connect, there will likely be data arriving from the
				# remote system.  This is one way of detecting when it's safe to
				# start sending data.
				while True:				
					if not crt.Screen.WaitForCursor(1):
						break
				# Once the cursor has stopped moving for about a second, we'll
				# assume it's safe to start interacting with the remote system.

				# Get the shell prompt so that we can know what to look for when
				# determining if the command is completed. Won't work if the prompt
				# is dynamic (e.g. changes according to current working folder, etc)

				prompt = get_prompt()
				# Write configuration before executing commands
				crt.Screen.Send("wr\n")
				crt.Screen.WaitForString("#")
				
				# Save to tftp
				#tftp = "copy running-config tftp:" + host + "\n"
				#crt.Screen.Send(tftp)
				#crt.Screen.WaitForString("?")
				#crt.Screen.Send("ipadress\n")
				#crt.Screen.WaitForString("?")
				#crt.Screen.Send("\n")
				#crt.Screen.WaitForString("#")
				
				# Send command to display everything at once
				crt.Screen.Send("terminal length 0\n")
				crt.Screen.WaitForString(prompt)
				# Send command to display info needed
				crt.Screen.Send("sh interface status | i Desktop\n")
				crt.Screen.WaitForString("\n")

				# Create an array of strings to wait for.
				waitStrs = ["\n", prompt]
				# Wait for the command to complete, by looking for the prompt to
				# appear once again.
				while True:
					# Wait for the linefeed at the end of each line, or the shell
					# prompt that indicates we're done.
					result = crt.Screen.WaitForStrings( waitStrs )
					# If we saw the prompt, we're done.
					if result == 2:
						break
					# Move down one line
					screenrow = crt.Screen.CurrentRow - 1
					# Get specific lines from the screen, where port and vlan info is located
					port = crt.Screen.Get(screenrow, 1, screenrow, 9).strip()
					vlan = crt.Screen.Get(screenrow, 43, screenrow, 46).strip()
					# Filter vlans to make sure it is a Desktop/Phone vlan(under 255)
					# Add ports and vlan to different arrays
					vlanId = int(vlan)
					if vlanId < 255:
						portArray.append(port)
						vlanArray.append(vlan)
					# Write to file
					fp.write(port + " " + vlan + os.linesep)
				
				# Close file
				fp.close()	
				# Send command for configuration
				crt.Screen.Send("conf t \n")
				
				# Loop thru both arrays and generate the command for each interface
				for i, j in zip(portArray,vlanArray):
					crt.Screen.WaitForString("#")
					# send command to configure interface reading from array
					crt.Screen.Send("int "+ i + "\n")
					crt.Screen.WaitForString("#")
					# read vlan id from array and add 400 to it, save it back to a string with command completed
					voicevlan = int(j) + 400	
					# Check if vlan array has voicevlan
					if voicevlan not in voiceArray:
						voiceArray.append(voicevlan)
					command = 'switchport voice vlan '
					command += str(voicevlan)
					command += "\n"
					# send command completed
					crt.Screen.Send(command)
					
				# Send commands to exit prompt all the way to logoff	
				crt.Screen.WaitForString("#")	
				crt.Screen.Send("exit\n")
				
				# change name for voicevlan
				# loop thru the array created with individual vlans
				for x in voiceArray:
					crt.Screen.WaitForString("#")
					command = 'vlan '
					command += str(x)
					command += "\n"
					crt.Screen.Send(command)
					crt.Screen.WaitForString("#")
					command = 'name VV_'
					command += str(x)
					command += "\n"
					crt.Screen.Send(command)
				# Exit prompt	
				crt.Screen.WaitForString("#")	
				crt.Screen.Send("end\n")
				crt.Screen.WaitForString("#")
				# Save configuration
				#crt.Screen.Send("wr\n")
				#crt.Screen.WaitForString("#")
				crt.Screen.Send("exit\n")
				
				# Wait one second
				crt.Sleep(1000)
				
				crt.Screen.Synchronous = False			
		#disconnect		
		crt.Session.Disconnect()
	
main()
