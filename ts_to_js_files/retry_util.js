/*
    * Utility APIs to retry an operations with configurable options.
    * If all attempts fail, throw the last encountered error.
*/
export async function retry_wrapper(function_to_execute, options = {}) {
    const { retries = 3, delayMs = 1000 } = options;
    let attempt = 1;
    while (attempt <= retries) {
        try {
            return await function_to_execute();
        }
        catch (err) {
            if (attempt === retries) {
                throw err;
            }
            console.warn(`Attempt #${attempt} failed. Encountered the following error: ${err}`);
            await new Promise(res => setTimeout(res, delayMs));
            attempt++;
        }
    }
    // Terminate with an exception, though this should never be reached,
    // since we will either return the function or throw an error in the loop
    throw new Error("Retry failed: reached maximum number of retries.");
}
//# sourceMappingURL=retry_util.js.map