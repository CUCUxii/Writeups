## GET aHEAD

Nos dan una web que tiene dos botones "elige rojo" y "elige azul", si le das a uno se cambia el color del fondo.
Con el azul lo toma como peticion POST a index.php mientras que verde es GET a index.php?. Inspeccionando el codigo fuente con el curl no he encontrado
ninguna flag ni ruta escondida. Examinando las peticiones con las herramientas del navegador tampoco encontre gran cosa. Estaba algo perdido hasta que me 
dio por hacer un curl -I para ver si habia mas informacion en los headers y di con la flag.
```bash
~:$ curl http://mercury.picoctf.net:53554  -I
HTTP/1.1 200 OK
flag: picoCTF{r3j3ct_th3_du4l1ty_2e5ba39f}
Content-type: text/html; charset=UTF-8
```
Tiene sentido porque el titulo del reto dice de HEAD y los colores daban la pista de probar a cambiar los metodos (get = rojo, post = azul )
Con burpsuite cambie a HEAD y me salio lo mismo (el el metodo que usa el curl -I).

--------------------------------------------------------------------

## Cookies

En esta web nos pone un "buscador de cookies" y la palabra "snickerdoodle" de ejemplo (supongo que sera una marca de cookies). Si pongo esa misma palabra
dice "I love snickerdoodle cookies!". Como estamos hablando todo el reto de las cookies, mire en el navegador en Cookies. Pone 0. Si le das a "home",
te sale el bscador otra vez y en cockies un -1. Si pongo otros numeros me sale el mensaje de "I love" otros tipos de cookies asi que supongo que 
habra que fuzzear o applicar algun tipo de sqli sencilla. Replicaos con curl la peticio:
```console
~:$ curl -s http://mercury.picoctf.net:6418 -H "Cookie: name=0"  -L | html2text
**** Cookies ****
×  That is a cookie! Not very special though...
I love snickerdoodle cookies!
```
Con un script de bash se pueden probar muchos numeros
```bash
for numero in $(seq 1 30); do
    peticion=$(curl -s "http://mercury.picoctf.net:6418/" -H "Cookie: name=$numero" -L | html2text )
    if ! echo $peticion | grep "Not very special" > /dev/null; then
        echo  "[Cookie nº -> $numero] $peticion" 
        exit 0
    fi  
done
```
```console
~:$ bash cookie.sh 
[Cookie nº -> 18] 
Flag: picoCTF{3v3ry1_l0v3s_c00k135_88acab36}
```
Para practicar quise hacer el equivalente en python.
```python
for number in range(20):
    req = requests.get("http://mercury.picoctf.net:6418/", cookies = {"name":str(number)})
    if not "That is a cookie! Not very special though..." in req.text:
        print(number)
```
--------------------------------------------------------------------

## Insp3ct0r

Aqui nos dan la web de alguien que acaba de empezar a programar "Mi primera web :)"
COn el *curl* (viendo el codigo fuente) tenemos 1/3 de la flag -> ```picoCTF{tru3_d3``` Tambien nos dan rutas a su .js y su .css, que al verlas
obetenemos el resto ```picoCTF{tru3_d3t3ct1ve_0r_ju5t_lucky?832b0699}```




