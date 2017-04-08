def str(num):
    prefix = '0x'
    suffix = 'L'
    data = ''
    while num > 0L:
        data = "%02x" % (num & 0xffL) + data
        num = num >> 8
    return prefix + data + suffix

