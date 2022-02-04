import json,requests,os
import settings
f = None

# Vérifie que le hash du bloc précédent est bien celui contenu dans le bloc que l'on veut ajouter.
def verif(new_block):
    b = open('blockchain.json', 'r+')
    blockchain = json.load(b)
    if new_block['prev'] != blockchain["block"][blockchain["length"]-1]["hash"]:
        return False
    return True

# Ecrasement du fichier json actuelle par les nouvelles valeurs.
# Nous retirons de notre liste l'adresse courante du noeuds car nous n'avons pas besoin de la sauvegarder.
# Vous avez du voir que nous verifions en double la longueur du tableau de nodes_ip c'est un problème à corriger.
def save_hardnodes(to_save,node_ip):
    if node_ip in to_save['nodes_ip']:
        to_save['nodes_ip'].remove(node_ip)
    global f
    to_save['length_validator_ip'] = len(to_save['nodes_ip'])
    f.seek(0)  # rewind
    print("to save : ", to_save)
    json.dump(to_save, f)
    f.truncate()

# Ajout d'un validator dans notre liste + sauvegarde du fichier json
def add_validator_to_bc(ip,current_node_ip):
    if ip not in settings.hard_nodes["validator_ip"]:
        settings.hard_nodes["validator_ip"].append(ip)
        settings.hard_nodes['length_validator_ip'] = len(settings.hard_nodes["validator_ip"])
        save_hardnodes(settings.hard_nodes,current_node_ip)
        print("validator to add : ", ip)
    return len(settings.hard_nodes["validator_ip"])

# Synchronise notre blockchain par rapport à la blockchain contenu dans tous les autres noeuds.
# Ici aucune vérification, nous regardons juste qu'elle blockchain est la plus grande. Si c'est
# la notre, nous envoyer notre blockchain au noeud que nous avons intérogé.
# Si sa blockchain est plus grande, nous mettons à jour notre blockchain.
def synchronise_run(blockchain,node_ip):
    need_to_write_in_file = False
    for node_ip_list in settings.hard_nodes["nodes_ip"]:
        if node_ip_list != node_ip:
            try:
                r = requests.get("http://"+node_ip_list+"/lengthblockchain")
            except:
                continue
            r = r.json()
            print("len bc : ", r)
            if blockchain != None and r['length'] < blockchain['length']:
                r = requests.post("http://"+node_ip_list+"/resetblockchain",json=blockchain).json()
            elif (blockchain != None and r['length'] > blockchain['length']) or blockchain == None:
                need_to_write_in_file = True
                r = requests.get("http://"+node_ip_list+"/getblockchain").json()
                blockchain = r["blockchain"]
    if need_to_write_in_file:
        b = open('blockchain.json', 'w')
        json.dump(blockchain, b)

# Ici nous paroutons chaque noeuds de notre liste.
# Pour chaque IP, nous allons lui demmande le nombde de validator qu'il a, si il en a plus que nous, nous remplacons notre liste par la sienne.
# Si il en a moins nous remplacons notre liste par la sienne.
# Bien sur vous l'aurez compris faire ainsi pose pleins de problèmes, comment etre sur que la liste qui contient le plus de vamidator est bonne ?
# Est ce que tous les validator fonctionne ?
# En remplacant tous les validators d'un coup on peut se retrouver avec des validators isolés.
# Dans l'idéal il faudrait pour chaque validator vérifier si il répond et si oui l'ajouter dans notre liste et si non passer au suivant.
# Pour des questions de facilité je suis parti du principe que chaque validator fonctionnaient
def update_validator_nodes(node_ip):
    need_to_write_in_file = False
    for node_ip_list in settings.hard_nodes["nodes_ip"]:
        if node_ip_list != node_ip:
            try:
                config_node = requests.get("http://"+node_ip_list+"/node")
            except:
                continue
            config_node = config_node.json()
            if config_node['config']['length_validator_ip'] < settings.hard_nodes['length_validator_ip']:
                r = requests.post("http://"+node_ip_list+"/resetvalidator",json=settings.hard_nodes['validator_ip']).json()
                print(r)
            else:
                need_to_write_in_file = True
                settings.hard_nodes['length_validator_ip'] = config_node['config']['length_validator_ip']
                settings.hard_nodes['validator_ip'] = config_node['config']['validator_ip']
    if need_to_write_in_file:
        save_hardnodes(settings.hard_nodes, node_ip)

# Premiere étape, on intéroge tous nos noeud connus pour avoir leur liste de noeuds.
# Puis pour chaque noeuds, on vérifie si on le connait. Si nous ne l'avons pas nous l'ajoutons à notre liste.
# Une fois notre liste mise à jour nous allons pouvoir mettre à jour la blockchain puis les validators.
def add_nodes_to_bc(current_node_ip):
    global f
    blockchain = None
    f = open('nodes_main.json', 'r+')
    need_save = False
    settings.hard_nodes = json.load(f)
    for node_ip in settings.hard_nodes["nodes_ip"]:
        try:
                r = requests.post("http://"+node_ip+"/node",json={'ip_to_add' : current_node_ip})
        except:
            continue
        r = r.json()
        for n in r['nodes']:
            if n not in settings.hard_nodes['nodes_ip']:
                need_save = True
                settings.hard_nodes['nodes_ip'].append(n)
                settings.hard_nodes['length_nodes_ip'] = int(settings.hard_nodes['length_nodes_ip']) + 1
    
    if os.path.isfile('blockchain.json') and os.stat('blockchain.json').st_size!=0:
        b = open('blockchain.json', 'r+')
        blockchain = json.load(b)
    synchronise_run(blockchain, current_node_ip)
    update_validator_nodes(current_node_ip)
    if need_save:
        save_hardnodes(settings.hard_nodes,current_node_ip)
    print("hard nodes : ", settings.hard_nodes)