// Only http(s) links may be rendered as anchors; javascript:, data: and the like are shown as text.
const isWebUrl = (value) => {
  try {
    const { protocol } = new URL(value);
    return protocol === 'http:' || protocol === 'https:';
  } catch (err) {
    return false;
  }
};

export default isWebUrl;
