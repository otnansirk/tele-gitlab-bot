#!/bin/sh
if [[ -n "$CI_COMMIT_TAG" ]]; then
  echo -e "\nsonar.projectVersion=$CI_COMMIT_TAG" >> sonar-project.properties
  echo -e "\nsonar.branch.name=$(git branch --remote --verbose --no-abbrev --contains | sed -rne 's/^[^\/]*\/([^\ ]+).*$/\1/p')" >> sonar-project.properties
else
  echo -e "\nsonar.projectVersion=latest" >> sonar-project.properties
fi