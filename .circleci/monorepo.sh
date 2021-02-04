#! /usr/bin/env bash

set -e

readonly REPO_TYPE=$( echo "${CIRCLE_REPOSITORY_URL}" | awk '{ match($0,/@github/) ? r="github" : r="bitbucket"; print r }' )
readonly PROJECT_SLUG="${REPO_TYPE}/${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}"

readonly SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
readonly TMP_DIR=${SCRIPT_DIR}/temp
readonly CONFIG_FILE=${SCRIPT_DIR}/monorepo.json
readonly CONCURRENCY=8

readonly TRIGGER_PARAM_NAME="trigger"

readonly BUILDS_FILE=${TMP_DIR}/builds.json
readonly DATA_FILE=${TMP_DIR}/data.json

# Get the list of configured packages or default ones.
function read_config_packages {
  c=$(jq --raw-output '(.packages // {}) | length' "$1")
  if [[ "${c}" == "0" ]]; then
    root_dir=$(jq --raw-output '.root // "packages"' "$1")
    find "${root_dir}/" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | awk -v d="${root_dir}" '{print $1 " " d "/" $1 "/"}'
  else
    jq -r '.packages | to_entries | map(([.key] + .value) | join(" ")) | join ("\n")' "$1"
  fi
}

# Download workflows status from CircleCI API (as JSON files).
function get_workflows {
  seq 0 100 $((($1 - 1) * 100)) | \
  awk \
    -v api="https://circleci.com/api/v1.1/project/${PROJECT_SLUG}" \
    -v tree="/tree/${CIRCLE_BRANCH}" \
    -v token="${CIRCLE_USER_TOKEN}" \
    -v dir="${TMP_DIR}/data." \
    '{ print $1 " " token " " api tree "?shallow=true&limit=100&offset=" $1 " " dir sprintf("%04d", $1) ".json" }' |\
  xargs -n4 -P${CONCURRENCY} bash -c 'curl -u "$1:" -L -Ss -o $3 -w "\tGET: [%{response_code}] %{url_effective}\n" $2'
}

# Creates a map of workflows and commit SHAs for which build passed.
function map {
  # Group by (workflow, commit sha, job name) and select
  # those workflows for which each job group contains at least one passed job.
  jq '.? |
    group_by(.workflows.workflow_name) |
      map({
        (.[0].workflows.workflow_name):
          group_by(.vcs_revision) |
            map({
              commit: .[0].vcs_revision,
              queued_at: .[0].queued_at,
              jobs: group_by(.workflows.job_name) | map({ success: any(.status == "success") })
            }) |
            map(select(.jobs | all(.success))) |
            sort_by(.queued_at) |
            reverse |
            map(.commit)
      }) |
      add |
      select (. != null)'
}

# Get the nearest commit from which the current branch was created.
function get_parent_commit {
  git_file="${TMP_DIR}/branches.txt"
  commit_sha=$1

  if [[ ! -f "${git_file}" ]]; then
    git show-branch --topo-order --sha1-name --current --remote > "${git_file}"
  fi

  remote_name=$(git remote show | head -n1)
  indents=$(\
    sed 's/].*/]/' "${git_file}" |                                                            # remove commit message
    awk '/^\-/ {exit} {print}' |                                                              # get lines until commits are listed
    awk -F '' -v b="[${remote_name}/${CIRCLE_BRANCH}]" 'match($0,/^ *\*/) || index($0, b)' |  # get only current branch and remote
    awk -F '' '{ t = length($0); sub("^ *",""); print t - length($0) + 1 }')                  # calculate indentation level

  head_indent=$(\
    sed 's/].*/]/' "${git_file}" |                                                            # remove commit message
    awk '/^\-/ {exit} {print}' |                                                              # get lines until commits are listed
    awk -F '' -v b="[${remote_name}/HEAD]" 'index($0, b)' |                                   # get origin/HEAD line
    awk -F '' '{ t = length($0); sub("^ *",""); print t - length($0) + 1 }')                  # calculate indentation level

  i1=$(echo "${indents}" | head -n1)
  i2=$(echo "${indents}" | tail -n1)
  i3=${head_indent:-$i1}

  sed 's/].*//' "${git_file}" |                                                                        # remove commit message
    awk -F '[' -v c="${commit_sha}" \
      'c == "null" || f; c!="null" && length($2) > 0 && index(c, $2) == 1 { f = 1; print }' |          # skip until first commit in current branch
    awk -F ''  -v i="${i1}" 'match(substr($0, i, 1), /[\+\-\*]/)' |                                    # filter only commits (including merges) related to current branch
    awk -F ''  -v i="${i1}" '{ print substr($0, 1, i - 1) " " substr($0, i + 1) }' |                   # excludes current branch
    awk -F ''  -v i="${i2}" '{ print substr($0, 1, i - 1) " " substr($0, i + 1) }' |                   # excludes current remote branch
    awk -F ''  -v i="${i3}" '{ print substr($0, 1, i - 1) " " substr($0, i + 1) }' |                   # excludes origin/HEAD branch
    awk -F ''  'gsub(/ /, "", $0)' |                                                                   # remove white-space
    awk -F ''  '/[\+\-]+\[/' |                                                                         # match only lines with commit or merge
    head -n1 |                                                                                         # get the top most found commit
    sed 's/^.*\[//'                                                                                    # leave only the commit sha text
}

# GIT diff each package to calculate the number of changed files.
function diff {
  parent_sha=$1
  builds_file=$2

  while read -r package paths; do
    last_build_sha=$(jq --raw-output --arg p "${package}" '.[$p][0]' "${builds_file}")
    if [[ "${last_build_sha}" != "null" && "x${last_build_sha}" != "x" ]]; then
      # diff changes since most recent successfull build for current workflow
      echo "$(git diff "${last_build_sha}"..HEAD --name-only -- ${paths} | wc -l)" "${last_build_sha:0:9}" built "${package}"
    elif [[ "x${parent_sha}" != "x" ]]; then
      # diff changes since parent branch commit sha
      echo "$(git diff "${parent_sha}"..HEAD --name-only -- ${paths} | wc -l)" "${parent_sha:0:9}" new "${package}"
    else
      # no builds and missing parent branch (detached?)
      echo 99999 - new "${package}"
    fi
  done
}

function print_status {
  echo -e "\nTrigger\tExists\tChanges\tParent\t\tPackage\n$(printf '=%0.s' {1..60})"
  echo "$1" | jq --raw-output '
    def colors:
    {
      "red": "\u001b[31m",
      "green": "\u001b[32m",
      "yellow": "\u001b[33m",
      "default": "\u001b[39m",
      "reset": "\u001b[0m",
    };
    def choose_color(a):
      if .changes == 99999 then colors.red
      elif .changes > 0 then colors.yellow
      elif .branch == "built" then colors.green
      else colors.default
    end;
    .[] | choose_color(.) +
      (if .changes > 0 then "[x]" else "[ ]" end) + "\t" +
      (if .branch == "built" then "[x]" else "[ ]" end) + "\t" +
      (.changes | tostring) + "\t" +
      .parent + "\t" +
      .package + colors.reset
    '
}

function create_request_body {
  echo "$1" |
  jq --raw-output --arg branch "${CIRCLE_BRANCH}" --arg trigger "${TRIGGER_PARAM_NAME}" --argjson params "${CI_PARAMETERS:-null}" '. |
    map(select(.changes > 0)) |
    reduce .[] as $i (($params // {}) * { ($trigger): false }; .[$i.package] = true) |
    { branch: $branch, parameters: . } |
    @json'
}

function create_pipeline {
  url="https://circleci.com/api/v2/project/${PROJECT_SLUG}/pipeline"
  echo -e "Trigger:\n\tUrl: ${url}\n\tData: $1"

  if [[ "${CI}" != "true" ]]; then
    echo "Not a CI environment. Skip pipeline trigger."
    exit 0
  fi;

  status_code=$(curl -s -u "${CIRCLE_USER_TOKEN}:" -o response.json -w "%{http_code}" -X POST --header "Content-Type: application/json" -d "$1" "${url}")

  if [ "${status_code}" -ge "200" ] && [ "${status_code}" -lt "300" ]; then
      echo "API call succeeded [${status_code}]. Response: "
      cat response.json
  else
      echo "API call failed [${status_code}]. Response: "
      cat response.json
      exit 1
  fi
}

function init {
  if [[ "x${CIRCLE_USER_TOKEN}" == "x" ]]; then
    echo "ENV variable CIRCLE_USER_TOKEN is empty. Please provide a user token."
    exit 1
  fi

  mkdir -p "${TMP_DIR}"
  if [[ ! -f ${CONFIG_FILE} ]]; then
    echo "No config file found at ${CONFIG_FILE}. Using defaults."
    echo "{}" > "${CONFIG_FILE}"
  fi
}

function get_builds {
  echo "Getting workflow status:"
  get_workflows "$(jq '.pages // 1' "${CONFIG_FILE}")"
  wait

  cat "${TMP_DIR}"/data.*.json | jq --slurp 'reduce inputs as $i (.; . += $i) | flatten' > "${DATA_FILE}"
  map < "${DATA_FILE}" > "${BUILDS_FILE}"
  echo "Created build-commit map ${BUILDS_FILE}"
}

function debug {
  echo -e "\n\nDEBUG INFORMATION"
  echo -e "\n\n=== Branches ==="
  cat "${TMP_DIR}/branches.txt"

  echo -e "\n\n=== Builds ==="
  cat "${BUILDS_FILE}"
}

function get_parent {
  first_commit_in_branch=$(jq --raw-output 'map(select(.vcs_revision)) | last | .vcs_revision' "${DATA_FILE}")
  echo "First built commit in branch: ${first_commit_in_branch}" >&2

  parent_commit=$(get_parent_commit "${first_commit_in_branch}")
  if [[ "x${parent_commit}" == "x" ]]; then
    # This could happen when branch is force pushed
    # and the build commit is no longer part of the history
    echo -e "\tCould not find parent commit relative to first build commit." >&2
    echo -e "\tEither branch was force pushed or build commit too old." >&2
    parent_commit=$(get_parent_commit null)
  fi
  echo "Parent commit: ${parent_commit}" >&2
  echo ${parent_commit}
}

function main {
  init
  get_builds
  git_parent_commit=$( get_parent )

  statuses=$(\
    read_config_packages "${CONFIG_FILE}" |
    diff "${git_parent_commit}" "${BUILDS_FILE}" |
    jq --raw-input --slurp \
      'split("\n") | map(select(. != "")) | map(split(" ")) | map({ package: .[3], parent: .[1], branch: .[2], changes: .[0] | tonumber })')

  print_status "${statuses}"
  changed_packages=$( echo "${statuses}" | jq '. | map(select(.changes > 0)) | length' )
  total_packages=$( echo "${statuses}" | jq '. | length' )

  echo "Number of packages changed: ${changed_packages} / ${total_packages}"

  if [[ "${changed_packages}" != "0" ]]; then
    create_pipeline "$( create_request_body "${statuses}" )"
  else
    echo "No changes in packages. Skip workflow trigger."
  fi

  if [[ "${MONOREPO_DEBUG}" == "true" ]]; then
    debug
  fi
}

main "${@}"
