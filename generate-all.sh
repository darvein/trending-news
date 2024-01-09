function summarize_articles_gpu() {
  #python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
  export TF_FORCE_GPU_ALLOW_GROWTH=true

  #for d in $(find output-articles/* -type d); do
    #clusterid=$(echo "$d" | tr -cd '[:digit:]')
    #python summarize-articles.py "${clusterid}" --debug 
  #done

    find output-articles/* -type d | xargs -I {} -P 1 bash -c 'clusterid=$(echo "{}" | tr -cd "[:digit:]"); python summarize-articles.py "${clusterid}" --debug'
}

function get_news_rss() {
  python3 get-rss-news.py urls-tech.txt
  if [ $? -ne 0 ]; then
    echo "The command failed."
    exit 1
  fi
}

function cluster_data() {
  python3 cluster-news.py --debug
  if [ $? -ne 0 ]; then
    echo "The command failed."
    exit 1
  fi
}

function generate_videos() {
  function run_python_script() {
    d="$1"
    clusterid=$(echo "$d" | tr -cd '[:digit:]')
    python3 generate-video2.py "${clusterid}" --debug
    echo "Done $d.txt"
  }

  find output-articles/* -type d | xargs -I {} -P 14 bash -c "$(declare -f run_python_script); run_python_script '{}'"
  
}

function get_images() {
  python3 unsplash-script.py --debug
}


function cleanup(){
  rm -rfv output-articles && mkdir output-articles
  rm -rfv output-videos/*.mp4
  rm -rfv out-titles-news.json
  rm -rfv images/*.jpg
  rm -rfv temp_images/*.jpg
}

function generate_titles() {
  titles="Mando una lista de oraciones separadas por 3 guiones, de cada una obten el sujeto principal en una o dos palabras. Al final dame una lista de palabras clave o sujetos separadas por coma."

  cd /home/n0kt/work/revista/trending-news
  for t in $(find . -name '*.title'); do 
    title=$(cat $t)
    titles="${titles} --- ${title}"
  done

  echo "${titles}" \
    | python3 chatgpt_text.py \
    | sed '/^[[:space:]]*$/d' \
    | tr -d '"' \
    | sed 's/:.*//' | sed 's/, /,/g' \
    | awk '{print substr ($0, 0, 100)}' \
    | tee output-articles/article-title.txt
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

function publish_wordpress() {
  python3 publish-wordpres.py --debug
}

function publish_youtube() {
  python3 publish-youtube.py --debug
}

source /opt/miniconda3/etc/profile.d/conda.sh
conda activate ri
CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib


#cleanup
#get_news_rss
cluster_data
#summarize_articles_gpu
#get_images
#generate_titles
#generate_videos
#publish_wordpress

conda deactivate
