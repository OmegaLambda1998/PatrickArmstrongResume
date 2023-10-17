import json
import argparse

def get_author_variations(author):
    *first, last = author.split()
    first = " ".join(first)
    Fdot_Last = f"{first[0]}. {last}"
    First_Last = f"{first} {last}"
    Lastcomma_Fdot = f"{last}, {first[0]}."
    F_Last = f"{first[0]} {last}"
    Lastcomma_First = f"{last}, {first}"
    return [Fdot_Last, First_Last, Lastcomma_Fdot, F_Last, Lastcomma_First]

def fix_Fdot_Last(author):
    return author

def fix_First_Last(author):
    *first, last = author.split()
    first = " ".join(first)
    return f"{first[0]}. {last}"

def fix_Lastcomma_Fdot(author):
    last, *f = author.split(", ")
    f = ", ".join(f)
    return f"{f} {last}"

def fix_F_Last(author):
    *f, last = author.split()
    f = " ".join(f)
    return f"{f}. {last}"

def fix_Lastcomma_First(author):
    last, *first = author.split(", ")
    first = ", ".join(first)
    return f"{first[0]}. {last}"

def fix_authors(authors, i):
    fs = [fix_Fdot_Last, fix_First_Last, fix_Lastcomma_Fdot, fix_F_Last, fix_Lastcomma_First]
    return [fs[i](author) for author in authors]

def wrap_element(orig_element, n):
    element = ""
    char_len = 0
    words = orig_element.split()
    for word in words: 
        element += word
        char_len += len(word)
        if word != words[-1]:
            if char_len > n:
                element += "\\\\"
                char_len = 0
            else:
                element += " "
    return element

def add_first_author(output, first_articles, first_other):
    with open(output, 'r') as f:
        lines = f.readlines()
    start_ind = [i for i in range(len(lines)) if "First Author" in lines[i]][0]
    s = ["\n"]
    for article in first_articles:
        title = wrap_element(article["title"], 27)
        journal = wrap_element(article["journal"], 27)
        author_list = article["authors"]
        if len(author_list) > 2:
            author_list = ", ".join(author_list[:2]).replace("'", "") + ", et. al."
        author_list = wrap_element(author_list, 27)
        year = article["last-modified-date"].split('-')[0]
        s.append(f"        \\publicationElement{{{title}}}{{{journal}}}{{{author_list}}}{{{year}}}\n")
    for article in first_other:
        title = wrap_element(article["title"], 27)
        journal = wrap_element(article["journal"], 27)
        author_list = article["authors"]
        if len(author_list) > 2:
            author_list = ", ".join(author_list[:2]).replace("'", "") + ", et. al."
        year = article["last-modified-date"].split('-')[0]
        s.append(f"        \\publicationElement{{{title}}}{{{journal}}}{{{author_list}}}{{{year}}}\n")
    result = "".join(lines[:start_ind+1] + s + lines[start_ind+1:])
    with open("complete_" + output, 'w') as f:
        f.write(result)

def add_co_author(output, co_articles, co_other):
    with open(output, 'r') as f:
        lines = f.readlines()
    start_ind = [i for i in range(len(lines)) if "Co-Author" in lines[i]][0]
    s = ["\n"]
    for article in co_articles:
        title = wrap_element(article["title"], 27)
        journal = wrap_element(article["journal"], 27)
        author_list = article["authors"]
        if len(author_list) > 2:
            author_list = ", ".join(author_list[:2]).replace("'", "") + ", et. al."
        author_list = wrap_element(author_list, 27)
        year = article["last-modified-date"].split('-')[0]
        s.append(f"        \\publicationElement{{{title}}}{{{journal}}}{{{author_list}}}{{{year}}}\n")
    for article in co_other:
        title = wrap_element(article["title"], 27)
        journal = wrap_element(article["journal"], 27)
        author_list = article["authors"]
        if len(author_list) > 2:
            author_list = ", ".join(author_list[:2]).replace("'", "") + ", et. al."
        year = article["last-modified-date"].split('-')[0]
        s.append(f"        \\publicationElement{{{title}}}{{{journal}}}{{{author_list}}}{{{year}}}\n")
    result = "".join(lines[:start_ind+1] + s + lines[start_ind+1:])
    with open(output, 'w') as f:
        f.write(result)


def main(args):
    with open(args.input, 'r') as f:
        papers = json.load(f)

    first_author = []
    co_author = []
    author = get_author_variations(args.author)
    for paper in papers:
        found_author = False
        for (i, auth) in enumerate(author):
            if auth in paper["authors"]:
                found_author = True
                is_first_author = auth == paper["authors"][0]
                paper["authors"] = fix_authors(paper["authors"], i)
                if is_first_author:
                    first_author.append(paper)
                else:
                    co_author.append(paper)
        if not found_author:
            print(f"Warning, don't have the author variation for paper: {paper}")

    print(f"Found {len(first_author)} first author papers")
    print(f"Found {len(co_author)} first co-author papers")

    first_articles = []
    first_other = []
    for paper in first_author:
        if paper["type"] in ["research-tool"]:
            first_other.append(paper)
        else:
            first_articles.append(paper)

    print(f"Found {len(first_articles)} first author articles")
    print(f"Found {len(first_other)} first author reports")

    co_articles = []
    co_other = []
    for paper in co_author:
        if paper["type"] in ["research-tool"]:
            co_other.append(paper)
        else:
            co_articles.append(paper)

    print(f"Found {len(co_articles)} co-author articles")
    print(f"Found {len(co_other)} co-author reports")

    add_first_author(args.output, first_articles, first_other)
    add_co_author("complete_" + args.output, co_articles, co_other)

    

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="json file containing papers to add to tex", type=str, required=True)
    parser.add_argument("-o", "--output", help="tex file to put papers into", type=str, required=True)
    parser.add_argument("-a", "--author", help="Your authorship name of the form Firstname Lastname (i.e. John Smith, Mary Jane, etc...)", type=str, required=True)
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    main(args)
