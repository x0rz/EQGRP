import re
import string

time = "+6"
regep = re.compile("^([+-]?)(([0-9]+)D)?(([0-9]+)H)?(([0-9]+)M)?(([0-9]+)S?)?$")
#x = re.compile("^\([-+]\)?\(\([0-9]*\)D\)?\(\([0-9]*\)H\)?\(\([0-9]*\)M\)?\(\([0-9]*\)S?\)?$")
x = regep.match(string.upper(time))
if x:
    times = [x.group(3), x.group(5), x.group(7), x.group(9)]
    for i in range(4):
        if times[i] == None or times[i] == "":
            times[i] = "0"
    time = eval(times[0]) * 86400 + eval(times[1]) * 3600 \
           + eval(times[2]) * 60 + eval(times[3])
    if x.group(1) == "-":
        time = time * -1
    print("%d\n" %(time))
else:
    print("bad\n")
