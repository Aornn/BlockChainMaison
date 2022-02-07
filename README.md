# BlockChainMaison

Code attaché à mon article pour comprendre la blockchain.
Pour le lancer il voud faudra python et flask.

1 - Lancer le premier noeud `python premierNoeud/noeuds.py` <br>
2 - Lancer le deuxieme noeud `python deuxiemeNoeud/noeuds.py`<br>
3 - Lancer le troisieme noeud `python troisiemeNoeud/noeuds.py`<br>
4 - Lancer le validator `python validator/validator.py`<br>

<br>

Pour ajouter un bloc faire une requete sur l'adresse IP d'un bloc sur l'endpoint "/sendblock". <br>
Exemple : <br>
```
curl --location --request POST 'http://127.0.0.1:5003/sendblock' \
--header 'Content-Type: application/json' \
--data-raw '{"Name" : "truc", "From" : "machin", "To" : "Bidule"}'
```
<br>

Pour comprendre l'interet de ce répo voici le billet de blog associé : 
https://medium.com/@rqueverdo/comprendre-la-blockchain-en-en-cr%C3%A9ant-une-soi-m%C3%AAme-ec71f2c4f914
