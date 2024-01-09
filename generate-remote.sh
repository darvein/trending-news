#!/bin/bash

function generate_data_remotely(){
  # Upload changes
  rsync -avP ./*.json ./*.py ./*.sh  halley:~/work/revista/trending-news/

  # Generate data
  #ssh halley 'cd ~/work/revista/trending-news; /bin/bash generate-all.sh'

  # Download data
  rm -vrf output-articles; \
    rsync -avP halley:~/work/revista/trending-news/output-articles .

  # Social network sharing
  scp -v \
    ./output-articles/final-tiktok.mp4 \
    ./output-articles/final-youtube.mp4 \
    ./output-articles/article-thumb.jpg \
    ./output-articles/article-title.txt \
    revista-wp-static:/var/www/html/WordPress/share/
}

function allow_my_current_public_ip(){
  SEC_GROUP_ID='sg-0aa52982fd1f17110'
  SEC_GROUP_RULE_ID='sgr-0d802e54dcb4d1715'

  SEC_GROUP_RULE_DESCRIPTION="Darvein SSH $CURRENT_IP"
  CURRENT_IP=$(curl --silent https://checkip.amazonaws.com)
  NEW_IPV4_CIDR="${CURRENT_IP}"/32

  aws-vault exec  -d 12h nextbrave -- \
    aws ec2 modify-security-group-rules --group-id ${SEC_GROUP_ID} --security-group-rules SecurityGroupRuleId=${SEC_GROUP_RULE_ID},SecurityGroupRule="{CidrIpv4=${NEW_IPV4_CIDR}, IpProtocol=tcp,FromPort=22,ToPort=22,Description=${SEC_GROUP_RULE_DESCRIPTION}}"
}

allow_my_current_public_ip
generate_data_remotely
