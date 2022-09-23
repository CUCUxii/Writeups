## Transformation

En este reto te dan una serie de caracteres chinos y tienes que sacar la flag de ahi. Tienes que trasadar cada caracter a entero (funcion *ord*) y de ahi a
dexadecimal, para luego decodear este ultimo y sacar la flag. Decirle al sistema que los numeros que ha utilizado para crear los caracteres chinos los
use para latinos
```console
~:$ python3
>>> enc = "灩捯䍔䙻ㄶ形楴獟楮獴㌴摟潦弸弰摤捤㤷慽"
>>> ''.join(([hex(ord(i)).replace('0x','') for i in enc]))
'7069636f4354467b31365f626974735f696e73743334645f6f665f385f30646463643937617d'
~:$ echo "7069636f4354467b31365f626974735f696e73743334645f6f665f385f30646463643937617d" | xxd -ps -r
picoCTF{16_bits_inst34d_of_8_0ddcd97a}
```
He utilizado un list comeprenesion (para ahorrarme bucles) que itera por cada caracter, lo pasa a entero (ord) y luego a hexadecimal (quitando los "0x").
Luego con el comando **xxd** de bash se traslada a ascii.

------------------------------------------------------------------
