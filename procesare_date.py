import pandas as pd
import os
from collections import Counter

def inlocuieste_nume(text):
    if pd.isna(text):
        return text
        
    # Dicționar cu înlocuiri
    inlocuiri = {
        # Corina
        'Corina': 'corina.cervinschi',
        
        # Constantin Dragomir
        'Dragomir C.': 'constantin.dragomir',
        'Dragomir ctin': 'constantin.dragomir',
        'Dragomir Ctin': 'constantin.dragomir',
        'Dragomir': 'constantin.dragomir',
        'CD': 'constantin.dragomir',
        'CC': 'constantin.dragomir',
        
        # Virgil Ionita
        'Virgil': 'virgil.ionita',
        'Ionita': 'virgil.ionita',
        
        # Andrei Barbu
        'andrei': 'andrei.barbu',
        'Andrei': 'andrei.barbu',
        
        # Valentin Ene
        'Brutus': 'valentin.ene',
        'Ene Valentin': 'valentin.ene',
        'Ene V.': 'valentin.ene',
        'Vali': 'valentin.ene',
        'Vali3': 'valentin.ene',
        'Valentin Ene': 'valentin.ene',
        'Ene': 'valentin.ene',
        'EV': 'valentin.ene',
        
        # Gabriel Mertea
        'gabi': 'gabriel.mertea',
        'Gabi': 'gabriel.mertea',
        
        # Valentin Dinu
        'Tali': 'valentin.dinu',
        'tali': 'valentin.dinu',

        # Laurentiu Henegariu
        'Laur': 'laurentiu.henegariu',
        'LH': 'laurentiu.henegariu',
        'Laurentiu': 'laurentiu.henegariu',
        'Laurentiu Henegariu': 'laurentiu.henegariu',
        'Laurentiu H': 'laurentiu.henegariu',
        'laur': 'laurentiu.henegariu'
    }
    
    # Dacă avem mai multe nume separate prin virgulă
    if ',' in text:
        # Separăm numele și le procesăm individual
        nume_lista = [nume.strip() for nume in text.split(',')]
        nume_procesate = []
        
        for nume in nume_lista:
            # Verificăm dacă numele trebuie înlocuit
            nume_nou = inlocuiri.get(nume, nume)
            nume_procesate.append(nume_nou)
            
        # Reunim numele înapoi cu virgulă
        return ', '.join(nume_procesate)
    else:
        # Dacă e un singur nume, îl înlocuim direct
        return inlocuiri.get(text.strip(), text)

def afiseaza_statistici_nume(df, coloana):
    # Extragem toate numele, inclusiv cele din câmpurile cu virgulă
    toate_numele = []
    for nume in df[coloana].dropna():
        if ',' in nume:
            toate_numele.extend([n.strip() for n in nume.split(',')])
        else:
            toate_numele.append(nume.strip())
    
    # Numărăm aparițiile
    counter = Counter(toate_numele)
    
    # Afișăm statisticile sortate după numărul de apariții
    print("\nStatistici nume (sortate după număr de apariții):")
    print("-" * 50)
    print(f"{'Nume':<30} {'Apariții':>10}")
    print("-" * 50)
    
    for nume, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        print(f"{nume:<30} {count:>10}")
    
    print("-" * 50)
    print(f"Total nume unice: {len(counter)}")
    print(f"Total apariții: {sum(counter.values())}")

def modifica_nume():
    csv_path = "Registru de Interventii.csv"
    try:
        # Citim CSV-ul cu separator ';'
        df = pd.read_csv(csv_path, encoding='windows-1252', sep=';')
        
        # Afișăm statistici înainte de modificare
        print("\nSTATISTICI ÎNAINTE DE MODIFICARE:")
        afiseaza_statistici_nume(df, 'PersonalITC')
        
        # Afișăm numele unice înainte de modificare
        print("Nume unice înainte de modificare:")
        nume_unice = sorted([x for x in df['PersonalITC'].unique() if pd.notna(x)])
        print(nume_unice)
        print("-" * 50)
        
        # Aplicăm funcția de înlocuire pentru fiecare câmp
        df['PersonalITC'] = df['PersonalITC'].apply(inlocuieste_nume)
        
        # Afișăm numele unice după modificare
        print("\nNume unice după modificare:")
        nume_unice_dupa = sorted([x for x in df['PersonalITC'].unique() if pd.notna(x)])
        print(nume_unice_dupa)
        print("-" * 50)
        
        # Afișăm statistici după modificare
        print("\nSTATISTICI DUPĂ MODIFICARE:")
        afiseaza_statistici_nume(df, 'PersonalITC')
        
        # Salvăm modificările în CSV
        df.to_csv(csv_path, encoding='windows-1252', sep=';', index=False)
        print("\nModificările au fost salvate în fișier!")
        
    except Exception as e:
        print(f"Eroare: {str(e)}")

if __name__ == "__main__":
    modifica_nume()
