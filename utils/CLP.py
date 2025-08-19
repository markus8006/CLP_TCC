from pymodbus.client import ModbusTcpClient
import ftplib


class __CLP:
    "CLPs genericos"
    def __init__(self, IP : str, UNIDADE : int, PORTA : int) -> None:
        self.IP = IP
        self.UNIDADE = UNIDADE
        self.PORTA = PORTA
        self.conctado = False
        self.client =  ModbusTcpClient(host=self.IP, port=self.PORTA)

    def conecatar(self):
        if self.client.connect():
            print(f"CLP conectado IP: {self.IP}")
            self.conctado = True
        else:
            print(f"Falha na conexão\nIP: {self.IP}\nPorta: {self.PORTA}")


    def deconectar(self):
        self.client.close()
        print(f"CLP desconectado IP {self.IP}")
        self.conctado = False



class CLPGen(__CLP):
    def __init__(self, IP : str, UNIDADE : int, PORTA : int) -> None:
        super().__init__(IP, UNIDADE, PORTA)

    
    def baixar_codigo(self, admin : str, senha : str) -> bool:
        ftp = ftplib.FTP(self.IP, admin, senha)
        with open('programa.hex', 'rb') as f:
            ftp.storbinary(f'STOR /programa{self.IP}.hex', f)


class CLPSiemens(__CLP):
    def __init__(self, IP : str, UNIDADE : int, PORTA : int) -> None:
        super().__init__(IP, UNIDADE, PORTA)

    def baixar_codigo(self):
        pass



        

if __name__ == "__main__":
    clp = CLPGen("192.168.0.1", 1, "501")
    clp.conecatar()