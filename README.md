# Song-Recommendation-System-for-Spotify-Playlist

## Data
The data used for this project comes from an open-source data set: <https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge> \\
There are over million playlists on the data set, and this system only uses two thousands of them.

## Database
The database used on this system is MongoDB. After the data pre-process, only playlist-id, track-url and artist-url are stored in the database from the original json file.

## Algorithm
The algorithm used for recommendation is user-based collaborative filtering algorithm. \\
Jaccard coefficient is used to calculate the similarity: $J(A,B)=\frac{|A \cap B|}{|A \cup B|}=\frac{|A \cap B|}{|A|+|B|-|A \cap B|}$ \\
Based on the similarity, find out all the songs in the k-closest playlists but not in the objective playlist, and rank them by the predicted-score: $p(u, i)=\sum_{v \in S(u, K) \cap N(i)} w_{u v} r_{v i}$\\
The top-n songs are the recommendation.

## Evaluation
Calculate the recall and precision according to the artist genres of the recommendatioon and objective playlist. \\
Artist genres are obtained from Spotify API using the artist-url.
