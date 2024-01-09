function summarize_articles_gpu() {
  source /opt/miniconda3/etc/profile.d/conda.sh 
  conda activate tf

  CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib
  #python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

  for d in $(find output-articles/* -type d); do
    clusterid=$(echo "$d" | tr -cd '[:digit:]')
    python summarize-articles.py "${clusterid}" --debug 
  done

  conda deactivate
}

function get_news_rss() {
  . venv/bin/activate

  python3 get-rss-news.py urls-tech.txt
  if [ $? -ne 0 ]; then
    echo "The command failed."
    exit 1
  fi

  deactivate
}

function cluster_data() {
  . venv/bin/activate

  python3 cluster-news.py --debug
  if [ $? -ne 0 ]; then
    echo "The command failed."
    exit 1
  fi

  deactivate
}

function generate_videos() {
  . venv/bin/activate
  
  function run_python_script() {
    d="$1"
    clusterid=$(echo "$d" | tr -cd '[:digit:]')
    python3 generate-video2.py "${clusterid}"
    echo "Done $d.txt"
  }

  find output-articles/* -type d | xargs -I {} -P 8 bash -c "$(declare -f run_python_script); run_python_script '{}'"
  
  deactivate
}

function get_images() {
  . venv/bin/activate
  python3 unsplash-script.py --debug
  deactivate
}

function generate_titles() {
  titles="Genera un título de hasta 100 letras sacando las palabras clave solamente de estas oraciones:\n"

  for t in $(find . -name '*.title'); do 
    title=$(cat $t)
    titles="${titles}\n${title}"
  done

  source /home/n0kt/Dropbox/Workspace/work/me/tts/venv/bin/activate
  echo "${titles}" \
    | python3 /home/n0kt/Dropbox/Workspace/work/me/tts/chatgpt_text.py \
    | sed '/^[[:space:]]*$/d' \
    | tr -d '"' \
    | sed 's/:.*//' | sed 's/, /,/g' \
    | awk '{print substr ($0, 0, 100)}' \
    | tee output-articles/article-title.txt
  deactivate
}

function publish_wordpress() {
  . venv/bin/activate
  python3 publish-wordpres.py
  deactivate
}

function publish_youtube() {
  . venv/bin/activate
  python3 publish-youtube.py
  deactivate
}

function join_videos() {
  . venv/bin/activate
  python3 join-videos.py --debug
  deactivate

  ffmpeg \
    -i output-articles/final-youtube.mp4 \
    -vcodec libx264 -crf 28 \
    output-articles/final-youtube-compressed.mp4
}

function get_images_delete(){
  . venv/bin/activate

  for d in $(find output-articles/* -type d); do
    clusterid=$(echo "$d" | tr -cd '[:digit:]')
    keywords=$(cat $d/$clusterid.txt.image)

    python unsplash-script.py "${clusterid}" "${keywords}" --debug
  done

  deactivate
}

function cleanup(){
  rm -rfv output-articles && mkdir output-articles
  rm -rfv output-videos/*.mp4
  rm -rfv out-titles-news.json
  rm -rfv images/*.jpg
  rm -rfv temp_images/*.jpg
}

#Get news
cleanup
get_news_rss
cluster_data
#summarize_articles_gpu
#get_images
#generate_videos

#generate_titles
#join_videos
#publish_wordpress
#publish_youtube
