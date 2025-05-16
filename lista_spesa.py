# Lista vuota
lista_spesa = []

print("Benvenuto nella tua lista della spesa!")

while True:
    print("\nScegli un'opzione:")
    print("1. Aggiungi un elemento")
    print("2. Rimuovi un elemento")
    print("3. Mostra la lista")
    print("4. Esci")

    scelta = input("Inserisci il numero della tua scelta: ")

    if scelta == "1":
        item = input("Cosa vuoi aggiungere? ")
        lista_spesa.append(item)
        print(f"{item} aggiunto alla lista.")
    
    elif scelta == "2":
        item = input("Cosa vuoi rimuovere? ")
        if item in lista_spesa:
            lista_spesa.remove(item)
            print(f"{item} rimosso dalla lista.")
        else:
            print(f"{item} non è nella lista.")
    
    elif scelta == "3":
        print("\nEcco la tua lista della spesa:")
        for i, item in enumerate(lista_spesa, start=1):
            print(f"{i}. {item}")
    
    elif scelta == "4":
        print("Arrivederci!")
        break
    
    else:
        print("Scelta non valida.")
