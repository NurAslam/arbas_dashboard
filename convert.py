import csv

def convert_pg_dump_to_csv(sql_file_path):
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_table = None
    csv_writer = None
    csv_file = None

    for line in lines:
        # Mencari awal blok data (contoh: COPY public."Delivery" (id, ...) FROM stdin;)
        if line.startswith('COPY '):
            parts = line.split(' ')
            
            # Mengambil nama tabel dan membersihkan tanda kutip/skema
            table_name = parts[1].replace('public.', '').replace('"', '')
            
            # Mengambil nama-nama kolom dari dalam kurung
            cols_start = line.find('(')
            cols_end = line.find(')')
            if cols_start != -1 and cols_end != -1:
                cols_str = line[cols_start+1 : cols_end]
                columns = [c.strip().replace('"', '') for c in cols_str.split(',')]
            else:
                columns = []

            # Membuat file CSV baru untuk tabel ini
            csv_file = open(f'{table_name}.csv', 'w', newline='', encoding='utf-8')
            csv_writer = csv.writer(csv_file)
            
            if columns:
                csv_writer.writerow(columns)
                
            current_table = table_name

        # Mencari penanda akhir blok data PostgreSQL (\.)
        elif current_table and line.strip() == '\\.':
            current_table = None
            if csv_file:
                csv_file.close()

        # Menulis baris data ke CSV
        elif current_table:
            # Data COPY PostgreSQL dipisahkan oleh Tab (\t)
            row = line.strip('\n').split('\t')
            # Mengubah \N (NULL) menjadi string kosong
            row = ["" if val == "\\N" else val for val in row]
            csv_writer.writerow(row)

    print("Proses konversi selesai! File CSV telah dibuat.")

# Jalankan script dengan memasukkan nama file SQL Anda
convert_pg_dump_to_csv('arbas.sql')