import requests
import json
import folium
import matplotlib.pyplot as plt
from collections import deque
import webbrowser

print('Welcome to the Restaurant Finder!')
print('Please input your coordinates (form: (x,y)):')

while True:
    user_input = input().strip().split(',')

    if len(user_input) != 2:
        print('Invalid input format. Please input coordinates in the form (x,y).')
        continue

    try:
        user_x = float(user_input[0][1:])
        user_y = float(user_input[1][:-1])
        print(f'Coordinates received: ({user_x}, {user_y})')
        break 
    except ValueError:
        print('Invalid coordinates. Please try again.')


yelp_api_key = 'skLkCn-T3n7MChhfKDzQn4dy0T2uefMBGPtauGVQ0U86oF1WVs8jnaM-pOtdgamu1fQysI8fROfPHsHlZUOZ6brQNSiqmGKC81Ta5W1S_Mxx6jYjuJAZg1nRc2Q8ZXYx'

def get_yelp_restaurant_data(yelp_api_key, location, categories, limit=1500):
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

        with open(cache_file, 'w') as file:
            json.dump(yelp_data, file)

    except Exception as e:
        print(f"An error occurred: {e}")

    return yelp_data

location = 'Michigan'
categories = 'restaurants'
yelp_data = get_yelp_restaurant_data(yelp_api_key, location, categories, limit=1500)

def get_yelp_reviews(yelp_api_key, business_id, yelp_data):
    if 'reviews' in yelp_data[business_id]:
        return yelp_data[business_id]['reviews']

    endpoint = f'https://api.yelp.com/v3/businesses/{business_id}/reviews'
    headers = {
        'Authorization': f'Bearer {yelp_api_key}',
    }

    try:
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        reviews = data.get('reviews', [])
        yelp_data[business_id]['reviews'] = reviews  # Cache the reviews
        return reviews
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


for business_id in yelp_data.keys():
    reviews = get_yelp_reviews(yelp_api_key, business_id, yelp_data)
    if reviews:
        yelp_data[business_id]['reviews'] = reviews

cache_file = 'yelp_cache.json'
with open(cache_file, 'w') as file:
    json.dump(yelp_data, file)

class TwoDTreeNode:
    def __init__(self, business_id, rating, distance_to_user, name, is_closed, reviews):
        self.business_id = business_id
        self.rating = rating
        self.distance_to_user = distance_to_user
        self.name = name
        self.is_closed = is_closed
        self.reviews = reviews
        self.left = None
        self.right = None

class TwoDTree:
    def __init__(self):
        self.root = None

    def insert(self, business_id, rating, distance_to_user, name, is_closed, reviews):
        self.root = self._insert_recursive(self.root, business_id, rating, distance_to_user, name, is_closed, reviews)

    def _insert_recursive(self, node, business_id, rating, distance_to_user, name, is_closed, reviews, depth=0):
        if node is None:
            return TwoDTreeNode(business_id, rating, distance_to_user, name, is_closed, reviews)

        axis = depth % 2
        if axis == 0:
            if rating < node.rating or (rating == node.rating and distance_to_user < node.distance_to_user):
                node.left = self._insert_recursive(node.left, business_id, rating, distance_to_user, name, is_closed, reviews, depth + 1)
            else:
                node.right = self._insert_recursive(node.right, business_id, rating, distance_to_user, name, is_closed, reviews, depth + 1)
        else:
            if distance_to_user < node.distance_to_user or (distance_to_user == node.distance_to_user and rating < node.rating):
                node.left = self._insert_recursive(node.left, business_id, rating, distance_to_user, name, is_closed, reviews, depth + 1)
            else:
                node.right = self._insert_recursive(node.right, business_id, rating, distance_to_user, name, is_closed, reviews, depth + 1)

        return node

tree = TwoDTree()


for business_id, data in yelp_data.items():
    rating = data['rating']
    business_x = data['coordinates']['latitude']
    business_y = data['coordinates']['longitude']
    distance_to_user = (((business_x - user_x) ** 2 + (business_y - user_y) ** 2) ** 0.5)*100
    
    name = data['name']
    is_closed = data['is_closed']
    reviews = data['reviews']
    tree.insert(business_id, rating, distance_to_user, name, is_closed, reviews)

# Function to visualize map showing restaurant locations
def show_restaurant_map(yelp_data):
    m = folium.Map(location=[42.3314, -83.0458], zoom_start=20)  # Initialize map at Detroit's location

    for business_id, data in yelp_data.items():
        latitude = data['coordinates']['latitude']
        longitude = data['coordinates']['longitude']
        name = data['name']
        folium.Marker([latitude, longitude], popup=name).add_to(m)

    m.save('restaurant_map.html')
    webbrowser.open('restaurant_map.html')
    return m


# Functions to rank restaurants by distance
def get_restaurant_info(node):
    reviews = []
    for review in node.reviews:
        reviews.append(review['text'])
    return {
        'Name': node.name,
        'Rating': node.rating,
        'Distance': node.distance_to_user,
        'Reviews': reviews
    }
def bfs(tree, n):
    closest_restaurants = []
    visited = set()

    queue = deque()
    queue.append(tree.root)

    while queue:
        node = queue.popleft()
        visited.add(node)

        closest_restaurants.append(node)

        if len(closest_restaurants) == n:
            return closest_restaurants

        if node.left and node.left not in visited:
            queue.append(node.left)

        if node.right and node.right not in visited:
            queue.append(node.right)

    return closest_restaurants

def rank_by_distance(tree, n):
    if not tree.root:
        return []

    nodes = bfs(tree, n)
    closest_restaurants = sorted(nodes, key=lambda node: node.distance_to_user)

    info_list = []
    for node in closest_restaurants:
        reviews=[]
        for review in node.reviews:
            reviews.append(review['text'])
        info_list.append(get_restaurant_info(node))

    return info_list


# Function to rank restaurants by ratings within distance

def search(node, max_distance, result):
    if not node:
        return

    if node.distance_to_user <= max_distance:
        search(node.left, max_distance, result)

        if node.distance_to_user <= max_distance:
            result.append(get_restaurant_info(node))

        search(node.right, max_distance, result)

def rank_by_ratings(tree, n, max_distance):
    if not tree.root:
        return []

    result = []
    search(tree.root, max_distance, result)

    result = sorted(result, key=lambda x: (x['Rating'], -x['Distance']), reverse=True)
    return result[:n]



# Function to create a bar chart with interaction
def create_interactive_barchart(yelp_data):
    ratings = {i: [] for i in range(11)}  # Dictionary to store restaurants by rating range

    # Organize restaurants by rating
    for business_id, data in yelp_data.items():
        rating = data['rating']
        ratings[int(rating * 2)].append((data['name'], data['url']))  # Scale ratings by 2 to map them to 0-10

    # Create a bar chart
    labels = [f"{i * 0.5}-{(i + 1) * 0.5}" for i in range(11)]
    x = range(len(labels))
    values = [len(ratings[i]) for i in range(11)]

    fig, ax = plt.subplots()
    bars = ax.bar(x, values, tick_label=labels)

    # Function to display restaurant names and URLs on clicking a bar
    def on_click(event):
        if event.xdata is not None and event.ydata is not None:
            index = int(event.xdata)
            if 0 <= index < len(ratings):
                restaurants = ratings[index]
                if restaurants:
                    print('\n')
                    print(f"Restaurants in the range of {labels[index]}:")
                    for name, url in restaurants:
                        print(f"- {name}: {url}")

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.xlabel('Rating Range')
    plt.ylabel('Number of Restaurants')
    plt.title('Restaurant Ratings Distribution')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()



choice = input("Choose an option (1. Map, 2. Rank by Distance, 3. Rank by Ratings, 4. Bar Chart): ")

if choice == '1':  # Map visualization
    restaurant_map = show_restaurant_map(yelp_data)

elif choice == '2':  # Rank by distance
    n = int(input("Enter the number of closest restaurants you want to see: "))
    closest_restaurants = rank_by_distance(tree, n)
    for restaurant in closest_restaurants:
        print(restaurant)
        print('\n')
    print(closest_restaurants)

elif choice == '3':  # Rank by ratings within distance
    n = int(input("Enter the number of top-rated restaurants you want to see: "))
    max_distance = float(input("Enter your acceptable maximum distance: "))
    top_rated_within_distance = rank_by_ratings(tree, n, max_distance)
    for restaurant in top_rated_within_distance:
        print(restaurant)
        print('\n')

elif choice == '4':  # Bar chart visualization
    create_interactive_barchart(yelp_data)


else:
    print("Invalid choice")
