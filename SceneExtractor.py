# SceneExtractor
import cv2
import numpy as np
from keras.applications.resnet50 import ResNet50, preprocess_input
from keras.preprocessing import image
from keras.models import Model
from sklearn.metrics.pairwise import cosine_similarity
from moviepy.video.io.VideoFileClip import VideoFileClip
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)
# 初始化 ResNet50 模型，只保留到平均池化层
base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
model = Model(inputs=base_model.input, outputs=base_model.output)

def extract_features(frame):
    img = cv2.resize(frame, (224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    features = model.predict(x)
    return features


def calculate_similarities_parallel(video_path):
    cap = cv2.VideoCapture(video_path)
    features_dict = OrderedDict()

    def process_frame(frame_number, frame):
        features = extract_features(frame)
        return frame_number, features

    with ThreadPoolExecutor() as executor:
        futures = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Get timestamp in seconds
            if timestamp.is_integer():  # Check if timestamp is an integer
                future = executor.submit(process_frame, timestamp, frame)
                futures.append(future)
        for future in futures:
            timestamp, features = future.result()
            if features is not None:
                features_dict[timestamp] = features

    similarities = []
    last_features = None
    logger.debug(f"features_dict:{features_dict}")
    logger.debug(f"len_features_dict:{len(features_dict)}")
    
    for frame_number, features in features_dict.items():
        if last_features is not None:
            sim = cosine_similarity(features, last_features)[0][0]
     
            similarities.append((frame_number, sim))
        last_features = features
    
    cap.release()
    return similarities


def detect_scene_changes(video_path, alpha=0):
    logger.debug(f"video_path:{video_path}")
    
    # check_scene_extraction(video_path, alpha)
    # check_video_and_similarities(video_path)
    similarities = calculate_similarities_parallel(video_path)
    logger.debug(f"similarities:{similarities}")
    similarity_scores = [sim for _, sim in similarities]
    mean_sim = np.mean(similarity_scores)
    print(mean_sim)
    std_sim = np.std(similarity_scores)
    threshold = mean_sim - alpha * std_sim
    logger.debug(f"similarity_scores:{similarity_scores}")
    similarity_scores = [sim for _, sim in similarities]
    percentile_2 = np.percentile(similarity_scores,99) 
    scene_changes = []
    for frame_number, sim in similarities:
        if sim <= threshold:
            time_in_seconds = frame_number 
            scene_changes.append(time_in_seconds)
    print(scene_changes)
    return scene_changes



