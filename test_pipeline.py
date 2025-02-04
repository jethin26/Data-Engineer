# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CO5W_EMCoNKnHo2n_ojMU0OLneXrUdld
"""

import unittest
import os
import pandas as pd
import sqlite3
import json

# Assume the actual code is in a module named pipeline.py
from pipeline import read_files_from_dir, parse_xml, window_by_datetime, process_to_RO, write_to_database, RO

class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory with sample XML files
        self.temp_dir = 'temp_dir'
        os.makedirs(self.temp_dir, exist_ok=True)
        self.xml_files = ['file1.xml', 'file2.xml']
        for file in self.xml_files:
            with open(os.path.join(self.temp_dir, file), 'w') as f:
                f.write('<event><order_id>1</order_id></event>')

    def tearDown(self):
        # Clean up the temporary directory
        for file in self.xml_files:
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_read_files_from_dir(self):
        # Test the function
        files = read_files_from_dir(self.temp_dir)
        self.assertEqual(len(files), 2)
        self.assertTrue(all(file.startswith('<event>') for file in files))

    def test_parse_xml(self):
        # Sample XML content
        xml_content = '<event><order_id>1</order_id><date_time>2023-01-01T12:00:00</date_time><status>Received</status><cost>50.0</cost><repair_details><technician>John Doe</technician><repair_parts><part name="Air Filter" quantity="1"/></repair_parts></repair_details></event>'

        # Test the function
        data = parse_xml([xml_content])
        self.assertEqual(len(data), 1)
        self.assertEqual(data['order_id'][0], '1')
        self.assertEqual(data['status'][0], 'Received')

    def test_window_by_datetime(self):
        # Sample DataFrame
        data = pd.DataFrame({
            'order_id': ['1', '2', '3'],
            'date_time': pd.to_datetime(['2023-01-01 12:00:00', '2023-01-01 13:00:00', '2023-01-02 12:00:00']),
            'status': ['Received', 'In Progress', 'Completed'],
            'cost': [50.0, 60.0, 70.0],
            'technician': ['John Doe', 'Jane Smith', 'Robert White'],
            'repair_parts': ['[("Air Filter", 1)]', '[("Oil Filter", 1)]', '[("Tire", 2)]']
        })

        # Test the function
        windowed_data = window_by_datetime(data, '1D')
        self.assertEqual(len(windowed_data), 2)  # Assuming 2 different days of data

    def test_process_to_RO(self):
        # Sample DataFrame
        data = pd.DataFrame({
            'order_id': ['1', '2'],
            'date_time': pd.to_datetime(['2023-01-01 12:00:00', '2023-01-01 13:00:00']),
            'status': ['Received', 'In Progress'],
            'cost': [50.0, 60.0],
            'technician': ['John Doe', 'Jane Smith'],
            'repair_parts': ['[("Air Filter", 1)]', '[("Oil Filter", 1)]']
        })

        # Test the function
        RO_list = process_to_RO({'2023-01-01': data})
        self.assertEqual(len(RO_list), 2)
        self.assertIsInstance(RO_list[0], RO)
        self.assertEqual(RO_list[0].order_id, '1')

    def test_write_to_database(self):
        # Sample list of RO objects
        RO_list = [
            RO('1', '2023-01-01 12:00:00', 'Received', 50.0, 'John Doe', [('Air Filter', 1)]),
            RO('2', '2023-01-01 13:00:00', 'In Progress', 60.0, 'Jane Smith', [('Oil Filter', 1)])
        ]

        # Test the function
        db_file = 'test_db.db'
        write_to_database(RO_list, db_file)

        # Check if data is written to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM repair_orders')
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 2)

        # Clean up
        conn.close()
        os.remove(db_file)

if __name__ == '__main__':
    unittest.main()