export default function replaceAllLoader(source) {
  const options = this.getOptions();
  const { replace } = options;
  let newSource = source;
  Object.entries(replace).forEach(([oldString, newString]) => {
    newSource = newSource.replaceAll(oldString, newString);
  });
  return newSource;
}
