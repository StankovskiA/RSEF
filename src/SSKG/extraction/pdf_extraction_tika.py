import collections
import logging
import os
import re
from tika import parser


def raw_read_pdf(pdf_path):
    if not pdf_path:
        return None
    try:
        path = os.path.expandvars(pdf_path)
        parsed = parser.from_file(path)
        content = parsed.get('content', None)
        if not content:
            logging.error("Issue when retrieving pdf content TIKA")
        return content
    except FileNotFoundError:
        logging.error(f"PDF file not found at path: {pdf_path}")
        return None
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {str(e)}")
        return None


def read_pdf_list(pdf_path):
    try:
        raw = parser.from_file(pdf_path)
        list_pdf_data = raw['content'].split('\n')
        # delete empty lines
        list_pdf_data = [x for x in list_pdf_data if x != '']

        return list_pdf_data

    except FileNotFoundError:
        logging.error(f"PDF file not found at path: {pdf_path}")
        return []
    except Exception as e:
        logging.error(f"An error occurred while reading the PDF: {str(e)}")
        return []


def get_possible_title(pdf):
    pdf_raw = raw_read_pdf(pdf)
    if not pdf_raw:
        return None
    return extract_possible_title(pdf_raw)


def extract_possible_title(pdf_raw_data):
    """
    Given raw data, this function attempts to extract a possible title.
    ASSUMPTION: The title is assumed to be the first non-line break character and ends with two line breaks \n\n
    :param pdf_raw_data: String of raw PDF data
    --
    :return: Possible title (String), or None if not found
    """
    poss_title = ""
    found_first_char = False
    previous_was_newline = False
    for i in pdf_raw_data:
        if not found_first_char:
            if i != '\n':
                found_first_char = True
                poss_title = poss_title + i
            else:
                continue
        else:
            if i == '\n' and previous_was_newline:
                return poss_title[:-1]
            elif i == '\n':
                previous_was_newline = True
                poss_title = poss_title + " "
            else:
                previous_was_newline = False
                poss_title = poss_title + i
    return None


def find_abstract_index(pdf_data):
    index = 0
    try:
        for line in pdf_data:
            if "abstract" in line.lower():
                if index < len(pdf_data):
                    return index
            index +=1
    except Exception as e:
        logging.warning(f"Failed to Extract the abstract {str(e)}")
        return None


def get_possible_abstract(pdf_data):
    try:
        index = find_abstract_index(pdf_data)
        if index:
            return ''.join(pdf_data[index:index+50])
    except Exception as e:
        print(e)


def find_github_in_abstract(pdf_data):
    abstract = get_possible_abstract(pdf_data)
    if abstract:
        return look_for_github_urls(abstract)


# regular expression to get all the urls, returned as a list
def get_git_urls(text):
    """
    Returns
    -------
    List Strings (urls)

    """
    urls_github = re.findall(r'(https?://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', text)
    urls_gitlab = re.findall(r'(https?://gitlab.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', text)
    # urls_zenodo = re.findall(r'(https?://zenodo.org/\S+)', text)
    # urls_bitbucket = re.findall(r'(https?://bitbucket.org/\S+)', text)
    # urls_sourceforge = re.findall(r'(https?://sourceforge.net/\S+)', text)
    # create a list with all the urls found
    urls = urls_github + urls_gitlab
    return urls

def raw_get_git_urls(raw_pdf_text):
    # TODO docstring
    text = re.sub(r'\n(?=[A-Za-z0-9_.-])', '', raw_pdf_text)
    urls_github = re.findall(r'(https?://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', text)
    urls_gitlab = re.findall(r'(https?://gitlab.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', text)
    urls = urls_github + urls_gitlab
    return urls

def clean_up_git_url(git_url_list):
    clean_urls = []
    for url in git_url_list:
        # Strip the trailing period if it exists
        if url.endswith('.'):
            url = url[:-1]
        # Strip '.git' if it exists
        elif url.endswith('.git'):
            url = url[:-4]
        clean_urls.append(url)

    return clean_urls


def look_for_github_urls(list_pdf_data):
    git_urls = []
    for value in list_pdf_data:
        results = get_git_urls(value)
        if results:
            git_urls.extend(results)
    git_urls = clean_up_git_url(git_urls)
    return git_urls


def raw_look_for_github_urls(raw_pdf_data):
    # TODO clean up and fix
    if not raw_pdf_data:
        return []
    urls = raw_get_git_urls(raw_pdf_data)
    if not urls:
        return []
    git_urls = clean_up_git_url(urls)
    return git_urls


def rank_elements(url_list):
    """
    Takes a list of strings

    Returns
    --------
    List of dictionary pairs. Key being the url (String) and the value the number of appearances
    Ordered, High to Low, Number of appearances
    """
    counts = collections.defaultdict(int)
    for url in url_list:
        counts[url] += 1
    return sorted(counts.items(),
                 key=lambda k_v: (k_v[1], k_v[0]),
                 reverse=True)


def ranked_git_url(pdf_data):
    """
    Creates  ranked list of GitHub urls and count pairs or false if none are available
    Returns
    -------
    List Strings (urls)
    --
    Else (none are found)
        False
    """
    try:
        github_urls = look_for_github_urls(pdf_data)
        if github_urls:
            return rank_elements(github_urls)
        else:
            return None
    except Exception as e:
        print(str(e))


def raw_ranked_git_url(raw_pdf_data):
    """
    Creates  ranked list of GitHub urls and count pairs or false if none are available
    Returns
    -------
    List Strings (urls)
    --
    Else (none are found)
        False
    """
    try:
        github_urls = raw_look_for_github_urls(raw_pdf_data)
        if github_urls:
            return rank_elements(github_urls)
        else:
            return None
    except Exception as e:
        print(str(e))



