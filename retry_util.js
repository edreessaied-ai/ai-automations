/*
    * Utility APIs to retry an operations with configurable options.
    * If all attempts fail, throw the last encountered error.
*/


async function retry(function_to_execute, { retries = 3, delayMs = 1000, backoff = 2 } = {}) {
  let attempt = 1;
  let currentDelay = delayMs;

  while (attempt <= retries) {
    try {
      return await function_to_execute();
    } catch (err) {
      if (attempt === retries) {
        throw err;
      }

      console.warn(`Attempt ${attempt} failed. Error: ${err.message}`, err);
      await new Promise(res => setTimeout(res, currentDelay));
      currentDelay *= backoff;
      attempt++;
    }
  }
}