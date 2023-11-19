import requests
import json
from bs4 import BeautifulSoup
import re

# 步骤 1: 设置Yelp API密钥
yelp_api_key = 'skLkCn-T3n7MChhfKDzQn4dy0T2uefMBGPtauGVQ0U86oF1WVs8jnaM-pOtdgamu1fQysI8fROfPHsHlZUOZ6brQNSiqmGKC81Ta5W1S_Mxx6jYjuJAZg1nRc2Q8ZXYx'

def get_yelp_restaurant_data(yelp_api_key, location, categories, limit=1500):
    # 检查缓存文件是否存在
    cache_file = 'yelp_cache.json'
    try:
        with open(cache_file, 'r') as file:
            yelp_data = json.load(file)
            return yelp_data
    except FileNotFoundError:
        yelp_data = {}

    endpoint = 'https://api.yelp.com/v3/businesses/search'
    headers = {
        'Authorization': f'Bearer {yelp_api_key}',
    }

    offset = 0

    try:
        while offset < limit:
            params = {
                'location': location,
                'categories': categories,
                'limit': min(50, limit - offset),
                'offset': offset,
            }

            response = requests.get(endpoint, headers=headers, params=params)
            data = response.json()

            businesses = data.get('businesses', [])
            for business in businesses:
                yelp_data[business['id']] = business

            if len(businesses) < min(50, limit - offset):
                break

            offset += 50

            if offset >= 1000:
                break

        # 将数据写入缓存文件
        with open(cache_file, 'w') as file:
            json.dump(yelp_data, file)

    except Exception as e:
        print(f"An error occurred: {e}")

    return yelp_data

# Example usage
location = 'Michigan'
categories = 'restaurants'
yelp_data = get_yelp_restaurant_data(yelp_api_key, location, categories, limit=1500)
print(yelp_data)


