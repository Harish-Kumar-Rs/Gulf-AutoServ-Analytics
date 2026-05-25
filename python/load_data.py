{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "13971d07-701b-4bc1-99b2-0786b8c3b59a",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Connected ✓\n"
     ]
    }
   ],
   "source": [
    "import psycopg2\n",
    "import pandas as pd\n",
    "import io, os\n",
    "\n",
    "DB_CONFIG = {\n",
    "    \"host\":     \"localhost\",\n",
    "    \"port\":     5433,\n",
    "    \"dbname\":   \"Gulf_Auto_Service\",\n",
    "    \"user\":     \"postgres\",\n",
    "}\n",
    "\n",
    "conn = psycopg2.connect(**DB_CONFIG)\n",
    "conn.autocommit = True\n",
    "cur = conn.cursor()\n",
    "print(\"Connected ✓\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "id": "8e55cb80-07ff-4d31-8d13-99f949a37c13",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "All tables created ✓\n"
     ]
    }
   ],
   "source": [
    "ddl_path = r\"C:/Users/MSI/Gulf-AutoServ-Analytics/ddl_create_tables.sql\"\n",
    "\n",
    "with open(ddl_path, \"r\") as f:\n",
    "    ddl_sql = f.read()\n",
    "\n",
    "cur.execute(ddl_sql)\n",
    "print(\"All tables created ✓\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "id": "46581cc1-e278-4023-a331-624934a4b517",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "  actuals_data\n",
      "  budget_data\n",
      "  five_year_plan\n",
      "  kpi_scorecard\n",
      "  partner_payments\n",
      "  pos_sales\n",
      "  vat_invoices\n",
      "  wallet_transactions\n"
     ]
    }
   ],
   "source": [
    "cur.execute(\"\"\"\n",
    "    SELECT table_name \n",
    "    FROM information_schema.tables \n",
    "    WHERE table_schema = 'public'\n",
    "    ORDER BY table_name\n",
    "\"\"\")\n",
    "for row in cur.fetchall():\n",
    "    print(f\"  {row[0]}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "id": "a57fb470-7a27-4cfb-9883-e19d322d420c",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Connection reset ✓\n"
     ]
    }
   ],
   "source": [
    "conn.rollback()\n",
    "conn.autocommit = False\n",
    "cur = conn.cursor()\n",
    "print(\"Connection reset ✓\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "id": "3bee0da2-9bc9-4341-8e4a-c9a5ae512fe0",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Column types fixed ✓\n"
     ]
    }
   ],
   "source": [
    "# Fix VARCHAR length\n",
    "cur.execute(\"ALTER TABLE vat_invoices ALTER COLUMN customer_trn TYPE VARCHAR(20)\")\n",
    "cur.execute(\"ALTER TABLE vat_invoices ALTER COLUMN branch_trn TYPE VARCHAR(20)\")\n",
    "conn.commit()\n",
    "print(\"Column types fixed ✓\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 28,
   "id": "7ad09254-f4c7-4dbb-b31e-ad75ac555195",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "  budget_data                  180 rows ✓\n",
      "  actuals_data                 180 rows ✓\n",
      "  five_year_plan                30 rows ✓\n",
      "  kpi_scorecard                 36 rows ✓\n",
      "  pos_sales                 14,304 rows ✓\n",
      "\n",
      "Final row counts:\n",
      "  budget_data                    180 rows\n",
      "  actuals_data                   180 rows\n",
      "  five_year_plan                  30 rows\n",
      "  kpi_scorecard                   36 rows\n",
      "  pos_sales                   14,304 rows\n",
      "\n",
      "All done ✓\n"
     ]
    }
   ],
   "source": [
    "import psycopg2\n",
    "import pandas as pd\n",
    "import io, os\n",
    "\n",
    "conn = psycopg2.connect(**DB_CONFIG)\n",
    "conn.autocommit = False\n",
    "cur = conn.cursor()\n",
    "\n",
    "CLEANED = r\"C:\\Users\\MSI\\Gulf-AutoServ-Analytics\\datasets\\cleaned\"\n",
    "\n",
    "# These 5 need reloading\n",
    "reload_tables = {\n",
    "    \"budget_data\":    \"budget_data.csv\",\n",
    "    \"actuals_data\":   \"actuals_data.csv\",\n",
    "    \"five_year_plan\": \"five_year_plan.csv\",\n",
    "    \"kpi_scorecard\":  \"kpi_scorecard.csv\",\n",
    "    \"pos_sales\":      \"pos_sales.csv\",\n",
    "}\n",
    "\n",
    "for table, csv_file in reload_tables.items():\n",
    "    df = pd.read_csv(os.path.join(CLEANED, csv_file))\n",
    "    df = df.where(pd.notnull(df), None)\n",
    "    buffer = io.StringIO()\n",
    "    df.to_csv(buffer, index=False, header=True, na_rep='')\n",
    "    buffer.seek(0)\n",
    "    cur.execute(f\"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE\")\n",
    "    cur.copy_expert(f\"COPY {table} FROM STDIN WITH CSV HEADER NULL ''\", buffer)\n",
    "    conn.commit()\n",
    "    print(f\"  {table:<25} {len(df):>6,} rows ✓\")\n",
    "\n",
    "# Final COUNT verify\n",
    "print(\"\\nFinal row counts:\")\n",
    "for table in reload_tables.keys():\n",
    "    cur.execute(f\"SELECT COUNT(*) FROM {table}\")\n",
    "    print(f\"  {table:<25} {cur.fetchone()[0]:>8,} rows\")\n",
    "\n",
    "cur.close()\n",
    "conn.close()\n",
    "print(\"\\nAll done ✓\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "efb843fd-bfee-4db7-ad6c-2a1a35acd913",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python [conda env:base] *",
   "language": "python",
   "name": "conda-base-py"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
