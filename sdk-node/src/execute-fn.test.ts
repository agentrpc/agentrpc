describe("executeFn", () => {
  it("should run a function with arguments", async () => {
    const fn = (val: { [key: string]: string }) => Promise.resolve(val.foo);
    const result = await fn({ foo: "bar" });
    expect(result).toBe("bar");
  });
});
