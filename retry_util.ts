/*
    * Utility APIs to retry an operations with configurable options.
    * If all attempts fail, throw the last encountered error.
*/

interface RetryOptions {
    retries?: number;
    delayMs?: number;
}

export async function retry_wrapper<T>(
    function_to_execute: () => Promise<T>,
    options: RetryOptions = {}
): Promise<T> {
    const { retries = 3, delayMs = 1000 } = options;
    let attempt = 1;

    while (attempt <= retries) {
        try {
            return await function_to_execute();
        } catch (err) {
            if (attempt === retries) {
                throw err;
            }

            console.warn(`Attempt #${attempt} failed. Encountered the following error: ${err}`);
            await new Promise(res => setTimeout(res, delayMs));
            attempt++;
        }
    }

    throw new Error("Retry failed"); // This should never be reached
}
