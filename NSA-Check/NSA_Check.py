import os
import csv

def checkRoot(rklist,failed,passed):
    i=0
    ksyms=0
    with open('rootkits') as f:
        for line in f:
            line=line.strip('\n')
            if '[' in line:
                ksyms=0
                currentTest=rklist[i]
                print("Testing " + currentTest)
                i=i+1
            elif 'Ksyms' in line:
                ksyms=1
            elif ksyms==1:
                ret = (os.popen("cat /proc/kallsyms | grep '{0}' && echo 'True' || echo 'False'".format(line)).readlines())
                if 'True\n' in ret:
                    ret = (os.popen("cat /proc/kallsyms | grep '{0}'".format(line)).readlines())
                    #debug
                    print("Ksym '{0}' found".format(line))
                    failed.append(str(currentTest) + ' | ' + str(line))
                    print(failed)

            else:
                ret = (os.popen("test -e {0} && echo 'True' || echo 'False'".format(line)).readlines())
                if  "True\n" in ret:
                    print("found")
                    failed.append(str(currentTest) + ' | ' + str(line))
                    print(failed)
                else:
                    passed.append(line)          
    f.close()
    return(rklist,failed,passed)
                
def main():
    failed = []
    passed = []
    rootkits=[]
    rklist=[]
    #open file to get stuff
    with open('rootkits') as f:
        for line in f:
            line=line.strip('\n')
            rootkits.append(line)
            if '[' in line:
                line=line.strip('\n')
                rklist.append(line)
    #close; will open later
    f.close()
    rklist,failed,passed = checkRoot(rklist,failed,passed)
    print("Summary: ")
    print(str(len(passed)) + " tests done")
    print("Number passed " + str(len(passed)))
    print("Number failed " + str(len(failed)))
    if str(len(failed)) == 0:
        print("Congratulations! Your system is clean! :) ")
    if range(len(failed)) >= 2:
        print("WARNING! WE HAVE DETECTED THE FOLLOWING ROOTKITS:")
        for i in range(len(failed)):
            print("{0} Status: FAILED".format(failed[i]))
if __name__ == '__main__':
    main()
