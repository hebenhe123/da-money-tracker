#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 metadata.csv 中筛选指定的 30 条记录用于评估
"""

import os
import csv

def main():
    # 指定要筛选的 doc_id 列表
    target_doc_ids = [
        '36b0f92b4b5e0fa345f52f21f9b2d912',
        '703235112eae33b90b85abe5785de8ba',
        '77ab847c58c49e430ec86e6647e55b30',
        'dc3aee0cbdf21460338158aae504969b',
        'b28b72f7a500395611cbd0f504a28c10',
        'a18c7118f38b85362c0ce4cbaa0623b8',
        'b1d5f6f1f63e521fa5d835715dc08f0c',
        '6a839db6d28e73294ab27c34515af091',
        '97310127b5333eedf8dbc02c5fe5bd62',
        'abe1925fe911604ba07ad5dbb87cfd5c',
        'caddeb69eabdbed765818dba1ae6aa72',
        '354ff82707f209d952182ab1fce9abb3',
        'c89fe063e655bcccb77939b1082eab45',
        '85c3e4358f65add9f94cada9c229894a',
        'c8b3ee9490312f9e5c885062ca184ef1',
        '8ba1f47dbbe88f4a69ed9d09b21263e1',
        'cb67e316a4f311616de11a9e0502f801',
        '8f35daa321fc462d9b293395e8e3cc52',
        '7d20a556470c4d21ecfca3f1e99c00eb',
        '5fd6f17d148a83b9a13ab0096d278163',
        '56c12a19ec58cb6672a4840cd455044f',
        '4f29e72b2539510cbbf7359fc187fb1f',
        '9462a156c6119e988dc82182938fd3b2',
        'ef858313e37ad5fec100528ed725e177',
        '4e048e663b243e681ebbf21310548fe4',
        '3f95dc45437b566b79516d26d9151284',
        'b8881909c909b21849abbb54a8612a68',
        '77d07f174876f0a0c8133ac9f8542cb4',
        '437a586cebd1d9fc59d010da6dfcea71',
        'e2a8d55e199af3109e6e54a158fc7668'
    ]
    
    # 输入输出路径
    input_path = 'data/metadata/metadata.csv'
    output_path = 'data/evaluation/sample_list.csv'
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 读取输入 CSV
    print(f"Reading input file: {input_path}")
    records = {}
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get('doc_id', '')
            if doc_id:
                records[doc_id] = row
    
    # 筛选记录
    filtered_records = []
    not_found_ids = []
    
    for doc_id in target_doc_ids:
        if doc_id in records:
            filtered_records.append(records[doc_id])
        else:
            not_found_ids.append(doc_id)
            print(f"Warning: doc_id not found - {doc_id}")
    
    # 保存结果
    if filtered_records:
        fieldnames = filtered_records[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_records)
        
        print(f"\n筛选完成！")
        print(f"目标记录数: {len(target_doc_ids)}")
        print(f"成功找到: {len(filtered_records)}")
        print(f"未找到: {len(not_found_ids)}")
        print(f"结果已保存到: {output_path}")
    else:
        print("Error: No records found!")

if __name__ == "__main__":
    main()
