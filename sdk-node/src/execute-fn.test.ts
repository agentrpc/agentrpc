import { executeFn } from "./execute-fn";

describe("executeFn", () => {
  it("should run a function with arguments", async () => {
    const fn = (val: { [key: string]: string }) => Promise.resolve(val.foo);
    const result = await fn({ foo: "bar" });
    expect(result).toBe("bar");
  });

  it("should authenticate a function with valid context", async () => {
    const fn = (val: { [key: string]: string }) => Promise.resolve(val.foo);
    const args = { foo: "bar" };
    const authenticate = (
      authContext: string,
      args: { [key: string]: string },
    ) => {
      return args.foo === authContext
        ? Promise.resolve()
        : Promise.reject(new Error("Unauthorized"));
    };

    const result = executeFn(fn, [args], authenticate, "bar");

    await expect(result).resolves.toEqual({
      content: "bar",
      functionExecutionTime: expect.any(Number),
      type: "resolution",
    });
  });

  it("should authenticate a function with invalid context", async () => {
    const fn = (val: { [key: string]: string }) => Promise.resolve(val.foo);
    const args = { foo: "bar" };
    const authenticate = (
      authContext: string,
      args: { [key: string]: string },
    ) => {
      return args.foo === authContext
        ? Promise.resolve()
        : Promise.reject(new Error("Unauthorized"));
    };

    const result = executeFn(fn, [args], authenticate, "not-bar");

    await expect(result).resolves.toEqual(
      expect.objectContaining({
        type: "rejection",
        content: expect.objectContaining({
          message: "Unauthorized",
        }),
      }),
    );
  });
});
