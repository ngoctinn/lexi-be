import boto3
import os

_dynamodb = boto3.resource("dynamodb")

def get_table():
    return _dynamodb.Table(os.environ["TABLE_NAME"])

def get_word_cache_table():
    return _dynamodb.Table(os.environ["WORD_CACHE_TABLE"])
