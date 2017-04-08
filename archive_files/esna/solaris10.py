import solaris9

class solaris10(solaris9.solaris9):
   def __init__(self, stackBase=0xfe0f4000L):
      self.stackBase = stackBase

   version = "Solaris 10"
