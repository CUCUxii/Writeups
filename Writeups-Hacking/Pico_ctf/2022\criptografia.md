
## Mod 26 

Reto de Criptografia (Rot 13)
Nivel: Muy facil

Nos dan una flag ```"cvpbPGS{arkg_gvzr_V'yy_gel_2_ebhaqf_bs_ebg13_Ncualgvd}"``` y en la descripcion nos mencionan ROT13 (cada letra se ha corrido 13
posiciones, o sea una "A" pasa a ser una "N"). En bash la operatoria para resolverlo es:
```console
~:$ echo "cvpbPGS{arkg_gvzr_V'yy_gel_2_ebhaqf_bs_ebg13_Ncualgvd}" | tr '[A-Za-z]' '[N-ZA-Mn-za-m]'
picoCTF{next_time_I'll_try_2_rounds_of_rot13_Aphnytiq}   # La flag :V
```

------------------------------------------------------------------------

## Mind your PS and QS

Aqui nos dan tres numeros "c", "n" y "e" y dicen que un pequeño e puede ser problematico. Estos numeros tienen que ver con las claves RSA, ya que se crean
efectuando alguna operatoria entre ellos.

```console
~:$  curl https://mercury.picoctf.net/static/3cfeb09681369c26e3f19d886bc1e5d9/values   
Decrypt my super sick RSA:
c: 8533139361076999596208540806559574687666062896040360148742851107661304651861689
n: 769457290801263793712740792519696786147248001937382943813345728685422050738403253
e: 65537
```
