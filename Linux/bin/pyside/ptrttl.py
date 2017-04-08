#!/usr/bin/python
import sys
import socket
import string
import struct

class NoOutput:
    def __init__(self):
        pass

    def write(self,arg1):
        pass

debug = 0
#debug = 1
if debug == 1:
    outputs = sys.stderr
else:
    outputs = NoOutput()

def HexConvert(data):
    global j
    ret = ''
    for i in range(len(data)):
        if i % 16 == 0 and i != 0:
            ret = ret + '\n' + padding
        myNum = struct.unpack("!H", '\000'+data[i:i+1])[0]
        ret = ret + "\\%o" % myNum
    j = j + len(data) - 1
    return ret

def NameConvertName(name):
    global j
    ret = ''
    sp = 0
    if type(name) != type(0):
        while name[sp:sp+1] != '\000':
            namelen = struct.unpack("!H",'\000' + name[sp:sp+1])[0]
            #print namelen
            if sp != 0:
                ret = ret + '.'
            for i in range(1,namelen+1):
                val = struct.unpack("!H", '\000' + name[sp+i:sp+i+1])[0]
                if val >= 32 and val < 127:
                    ret = ret + name[sp+i:sp+i+1]
                else:
                    raise TypeError, name
            sp = sp+1+namelen
    j = j + sp
    return ret
        

def NameConvert(name,len=2):
    try:
        return NameConvertName(name)
    except:
        return HexConvert(name[:len])
        
# Open the sockey
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.setblocking(1)

# Get the server ip
try:
    cmd = sys.argv[1]
except:
    sys.stderr.write("Usage: %s <dns_server_ip> [lookup_ip [filename]]\n\n" %\
                     (sys.argv[0]))
    sys.exit()
dest = (socket.gethostbyname(cmd),53)

# Get the lookup ip
try:
    ip = sys.argv[2]
except:
    ip = cmd

# Fill the DNS Header
data = struct.pack("!HHHHHH",
                   0x1234, #id
                   0x0000, #QR, Op, AA, TC, RD, RA, RCODE
                   0x1,    # number of questions
                   0x0,    # number of answers
                   0x0,    # number of name servers
                   0x0)    # number of additional records

# Form the Query
ip = string.splitfields(ip,'.')
cmd = string.splitfields(cmd,'.')
if len(ip) != 4:
    sys.exit()

for i in range(4):
    data = data + chr(len(ip[3-i])) + ip[3-i]
data = data + chr(7) + 'in-addr' + chr(4) + 'arpa'

data = data + '\000' + struct.pack("!HH",
                                   12,  #type
                                   1)   #class
# Send the Query and receive the response
sock.sendto(data,dest)
data,who = sock.recvfrom(512)

# Parse the header
entries = struct.unpack("!HHHH",data[4:12])
rawoutput = data[2:12]

j=12
datap = j
res = ''
# Read the Query Section
for i in range(entries[0]):
    outputs.write( "Query:\n" )
    Name = NameConvert(data[j:])
    outputs.write("  Name: " + Name + '\n')
    outputs.write("  Type: %d\n" % (struct.unpack("!H", data[j+1:j+3])[0]) )
    outputs.write("  Class: %d\n" % (struct.unpack("!H", data[j+3:j+5])[0]))
    if i == 0:
        res = res + 'rule 0.0.0.0 0.0.0.0 7200 PTR IN "'+Name+'" 0x0480L\n'
    j = j + 5
    rawoutput = rawoutput + data[datap:j]
    datap = j

# Read the Answer Section
for i in range(entries[1]):
    outputs.write( "Answer:\n" )
    Name = NameConvert(data[j:])
    rawoutput = rawoutput + data[datap:j+5] + struct.pack("!L",30)
    datap = j+9
    outputs.write( "  Name: " + Name + '\n' )
    outputs.write("  Type: %d\n" % (struct.unpack("!H", data[j+1:j+3])[0]) )
    outputs.write("  Class: %d\n" % (struct.unpack("!H", data[j+3:j+5])[0]))
    outputs.write("  TTL: %d\n" % (struct.unpack("!L", data[j+5:j+9])[0]) )
    DataLen = struct.unpack("!H", data[j+9:j+11])[0]
    outputs.write( "  Data length: %d\n" % (DataLen) )
    Data = NameConvert(data[j+11:],DataLen)
    outputs.write( "  Data: " + Data + '\n' )
    if i == 0:
        res = res + 'ans "' + Name + '" PTR IN 30 "' + Data + '"\n'
    j = j + 12
    rawoutput = rawoutput + data[datap:j]
    datap = j

# Read the Authority Section
for i in range(entries[2]):
    outputs.write( "Authority:\n" )
    OldData1 = j+12
    Name = NameConvert(data[j:])
    outputs.write("  Name: " + Name + '\n' )
    outputs.write("  Type: %d\n" % (struct.unpack("!H", data[j+1:j+3])[0]) )
    outputs.write("  Class: %d\n" % (struct.unpack("!H", data[j+3:j+5])[0]))
    outputs.write("  TTL: %d\n" % (struct.unpack("!L", data[j+5:j+9])[0]) )
    DataLen = struct.unpack("!H", data[j+9:j+11])[0]
    outputs.write( "  Data length: %d\n" % (DataLen) )
    Data = NameConvert(data[j+11:],DataLen)
    outputs.write( "  Data: " + Data + '\n')
    if i == 0:
        OldData = OldData1
        res = res + 'auth "\\300\\%o' % (len(ip[3])+13) + '" NS IN 7200 "' + Data + '"\n'
    j = j + 12
    rawoutput = rawoutput + data[datap:j]
    datap = j

# Read the Additional Section
for i in range(entries[3]):
    outputs.write( "Additional:\n" )
    Name = NameConvert(data[j:])
    outputs.write("  Name: " + Data + '\n' )
    outputs.write("  Type: %d\n" % (struct.unpack("!H", data[j+1:j+3])[0]) )
    outputs.write("  Class: %d\n" % (struct.unpack("!H", data[j+3:j+5])[0]))
    outputs.write("  TTL: %d\n" % (struct.unpack("!L", data[j+5:j+9])[0]) )
    DataLen = struct.unpack("!H", data[j+9:j+11])[0]
    outputs.write( "  Data length: %d\n" % (DataLen) )
    Data = HexConvert(data[j+11:j+11+DataLen])
    outputs.write( "  Data: " + Data + '\n')
    if i == 0:
        res = res + 'add "\\300\\%o' %(OldData)  + \
              '" A IN 7200 "\\%o\\%o\\%o\\%o' %\
              (eval(cmd[0]),eval(cmd[1]),eval(cmd[2]),eval(cmd[3]))+ '"\n'
    j = j + 12
    rawoutput = rawoutput + data[datap:j]
    datap = j

res = res + "set active\n"
sys.stdout.write( "File size: %d bytes\n" % len(rawoutput))
# Output the result
try:
    filename = sys.argv[3]

    file = open(filename,'w')
#    file.write(res)
#    file.close()
    file.write(rawoutput)
    file.close()
except:
    sys.stdout.write( rawoutput )
#    sys.stdout.write( res )
#    file = open("testfile.raw",'w')
