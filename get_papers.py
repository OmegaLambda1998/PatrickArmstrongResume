import requests
import xmltodict
import argparse
import subprocess
import ads
import arxiv
import tqdm
from joblib import Parallel, delayed
from multiprocessing import cpu_count
import json
import re

def get_authors_from_doi(doi):
    response = subprocess.run(["doi2bib", doi], capture_output=True, text=True).stdout
    patter = re.compile(r'author={([^}]*)}')
    match = patter.search(response)
    if match:
        author_list = match.group(1)
        authors = [author.strip() for author in author_list.split(" and ")]
    else:
        print(f"No bibtex information for doi: {doi}")
        return None
    return authors 

def get_authors_from_bibcode(bibcode):
    response = list(ads.SearchQuery(bibcode=bibcode))
    if len(response) == 0:
        print(f"No ads information for bibcode: {bibcode}")
        return None
    authors = response[0].author
    return authors

def get_authors_from_arxiv(arxiv_id):
    response = list(arxiv.Search(id_list=[arxiv_id]).results())
    if len(response) == 0:
        print(f"No arxiv information for arxiv_id: {arxiv_id}")
        return None
    authors = [author.name for author in response[0].authors]
    return authors

def get_papers(content):
    data = xmltodict.parse(content.decode('utf-8'))['activities:works']['activities:group']
    def task(paper_data):
        paper = {}
        # Get the last-modified-date
        paper["last-modified-date"] = paper_data["common:last-modified-date"]
        # Get all external ids (doi, arxiv-id, bibcode, etc...)
        external_ids = paper_data["common:external-ids"]["common:external-id"]
        if type(external_ids) is not list:
            external_ids = [external_ids]
        for id in external_ids:
            id_type = id["common:external-id-type"]
            id_value = id["common:external-id-value"]
            paper[id_type] = id_value
        # Get actual paper data 
        work_summary = paper_data["work:work-summary"]
        if type(work_summary) is list:
            work_summary = work_summary[-1]
        paper["title"] = work_summary["work:title"]["common:title"]
        paper["type"] = work_summary["work:type"]
        paper["journal"] = work_summary["work:journal-title"]
        # Attempt to get bibtex citation, which includes author information
        authors = None
        if "doi" in paper.keys():
            #print(f"Getting authors for paper: '{paper['title']}' via doi")
            authors = get_authors_from_doi(paper["doi"])
        if ("bibcode" in paper.keys()) and (authors is None):
            #print(f"Getting authors for paper: '{paper['title']}' via bibcode")
            authors = get_authors_from_bibcode(paper["bibcode"])
        if ("arxiv" in paper.keys()) and (authors is None):
            #print(f"Getting authors for paper: '{paper['title']}' via arxiv")
            authors = get_authors_from_arxiv(paper["arxiv"])
        if authors is None:
            print(f"Warning can't get authors for paper: '{paper['title']}', missing doi, bibcode or arxiv-id.")
            print(paper)
        paper["authors"] = authors
        return paper
    papers = Parallel(n_jobs=cpu_count())(delayed(task)(paper_data) for paper_data in tqdm.tqdm(data))
    #papers = [task(paper_data) for paper_data in data]
    return papers 

def find_duplicates(papers):
    titles = []
    for paper in papers:
        title = paper['title'].upper()
        if title in titles:
            print(f"Warning duplicate title found: {title}")
        titles.append(title)


def organise_papers(papers, grouping):
    organised_papers = {}
    for paper in papers:
        work_summary = paper['work:work-summary']
        if type(work_summary) is list:
            work_summary = work_summary[-1]
        paper_type = work_summary['work:type']
        if paper_type not in organised_papers.keys():
            organised_papers[paper_type] = []
        organised_papers[paper_type].append(paper)
    return organised_papers

def main(args):
    api_url = f'https://pub.orcid.org/v3.0/{args.orcid}/works'
    response = requests.get(api_url)
    if response.status_code == 200:
        content = response.content
    else:
        print(f"Warning, response has status code: {response.status_code}")
        return None
    papers = get_papers(content) 
    print(f"Found {len(papers)} papers")
    for paper in papers:
        if paper['title'] is None:
            print(paper)
    find_duplicates(papers)
    with open(args.output, "w") as f:
        json.dump(papers, f, indent=4)
        
     
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-id", "--orcid", help="Specify your orcid id", type=str, required=True)
    parser.add_argument("-o", "--output", help="File to save papers to", type=str, default="papers.json")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    main(args)
