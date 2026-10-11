const authTabs = document.querySelectorAll(
    "[data-auth-view]"
);

const loginForm = document.getElementById(
    "loginForm"
);

const registerForm = document.getElementById(
    "registerForm"
);

const authMessage = document.getElementById(
    "authMessage"
);

let loginFormTouched = false;


/*
Display login or registration messages.
*/
function setMessage(message, type = "") {
    authMessage.textContent = message;

    authMessage.classList.remove(
        "success",
        "error"
    );

    if (type) {
        authMessage.classList.add(type);
    }
}


/*
Reset password visibility and spider mask.
*/
function resetPasswordAppearance(form) {
    form
        .querySelectorAll(".spider-password")
        .forEach((input) => {
            input.type = "password";

            const toggle = input
                .closest(".password-wrap")
                .querySelector(
                    ".password-toggle"
                );

            toggle.classList.remove(
                "password-visible"
            );

            toggle.setAttribute(
                "aria-label",
                "Show password"
            );

            updateSpiderMask(input);
        });
}


/*
Clear the login form so the username
and password are not already filled.
*/
function clearLoginForm() {
    loginForm.reset();

    loginForm
        .querySelectorAll("input")
        .forEach((input) => {
            if (input.type === "checkbox") {
                input.checked = false;
            } else {
                input.value = "";
            }
        });

    resetPasswordAppearance(loginForm);
}


/*
Switch between Sign in and Create account.
*/
function selectAuthView(view) {
    const showLogin = view === "login";

    loginForm.hidden = !showLogin;
    registerForm.hidden = showLogin;

    authTabs.forEach((tab) => {
        const selected =
            tab.dataset.authView === view;

        tab.classList.toggle(
            "active",
            selected
        );

        tab.setAttribute(
            "aria-selected",
            String(selected)
        );
    });

    setMessage("");
}


authTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        selectAuthView(
            tab.dataset.authView
        );
    });
});


/*
Convert FastAPI validation errors into
a readable message.
*/
function getApiError(
    data,
    fallbackMessage
) {
    if (
        typeof data?.detail === "string"
    ) {
        return data.detail;
    }

    if (Array.isArray(data?.detail)) {
        return data.detail
            .map((error) => error.msg)
            .filter(Boolean)
            .join(" ");
    }

    return fallbackMessage;
}


/*
Safely read JSON responses.
*/
async function readJsonResponse(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}


/*
Display small spiders instead of the
browser's normal password dots.
*/
function updateSpiderMask(input) {
    const wrapper = input.closest(
        ".password-wrap"
    );

    if (!wrapper) {
        return;
    }

    const mask = wrapper.querySelector(
        ".spider-mask"
    );

    if (!mask) {
        return;
    }

    mask.replaceChildren();

    if (
    input.type === "text" ||
    input.value.length === 0
) {
    input.classList.remove("is-masked");
    mask.classList.remove("has-focus");
    return;
}

    input.classList.add("is-masked");

    const maximumVisibleSpiders = 18;

    const visibleSpiders = Math.min(
        input.value.length,
        maximumVisibleSpiders
    );

    for (
        let index = 0;
        index < visibleSpiders;
        index += 1
    ) {
        const spider =
            document.createElement("span");

        spider.className =
            "password-spider";

        spider.textContent = "🕷";

        mask.appendChild(spider);
    }

    if (
        input.value.length >
        maximumVisibleSpiders
    ) {
        const overflow =
            document.createElement("span");

        overflow.className =
            "password-spider";

        overflow.textContent = "…";

        mask.appendChild(overflow);
    }

    mask.classList.toggle(
        "has-focus",
        document.activeElement === input
    );
}


/*
Activate spider masking for all
password fields.
*/
document
    .querySelectorAll(".spider-password")
    .forEach((input) => {
        input.classList.add("is-masked");

        [
            "input",
            "focus",
            "blur",
            "change"
        ].forEach((eventName) => {
            input.addEventListener(
                eventName,
                () => {
                    updateSpiderMask(input);
                }
            );
        });

        updateSpiderMask(input);
    });


/*
Show or hide a password when its
eye button is selected.
*/
document
    .querySelectorAll(".password-toggle")
    .forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                const wrapper =
                    button.closest(
                        ".password-wrap"
                    );

                const input =
                    wrapper.querySelector(
                        ".spider-password"
                    );

                const passwordIsHidden =
                    input.type === "password";

                input.type = passwordIsHidden
                    ? "text"
                    : "password";

                button.classList.toggle(
                    "password-visible",
                    passwordIsHidden
                );

                button.setAttribute(
                    "aria-label",
                    passwordIsHidden
                        ? "Hide password"
                        : "Show password"
                );

                updateSpiderMask(input);
                input.focus();
            }
        );
    });


/*
Track whether the user has started
entering login information.
*/
loginForm
    .querySelectorAll("input")
    .forEach((input) => {
        input.addEventListener(
            "input",
            () => {
                loginFormTouched = true;
            }
        );

        input.addEventListener(
            "change",
            () => {
                loginFormTouched = true;
            }
        );
    });


/*
Clear browser-restored login values when
the login page is opened.
*/
window.addEventListener(
    "pageshow",
    () => {
        window.setTimeout(
            () => {
                if (!loginFormTouched) {
                    clearLoginForm();
                }
            },
            150
        );
    }
);


/*
Sign in.
The Secure login checkbox is sent to
FastAPI as remember_me.
*/
loginForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        if (!loginForm.checkValidity()) {
            loginForm.reportValidity();
            return;
        }

        const submitButton =
            loginForm.querySelector(
                ".submit-button"
            );

        submitButton.disabled = true;

        setMessage("Signing in...");

        const payload = {
            username:
                loginForm.elements.username
                    .value
                    .trim(),

            password:
                loginForm.elements.password
                    .value,

            remember_me: Boolean(
                loginForm.elements.remember
                    .checked
            )
        };

        try {
            const response = await fetch(
                "/api/auth/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    body: JSON.stringify(
                        payload
                    )
                }
            );

            const data =
                await readJsonResponse(
                    response
                );

            if (!response.ok) {
                throw new Error(
                    getApiError(
                        data,
                        "Login failed."
                    )
                );
            }

            setMessage(
                "Login successful!",
                "success"
            );

            window.location.assign("/");

        } catch (error) {
            setMessage(
                error.message ||
                    "Unable to sign in.",
                "error"
            );

        } finally {
            submitButton.disabled = false;
        }
    }
);


/*
Create a new account.
After registration, return to the
Sign in tab with empty fields.
*/
registerForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        if (!registerForm.checkValidity()) {
            registerForm.reportValidity();
            return;
        }

        const username =
            registerForm.elements.username
                .value
                .trim();

        const password =
            registerForm.elements.password
                .value;

        const confirmation =
            registerForm.elements
                .confirm_password
                .value;

        if (username.length < 3) {
            setMessage(
                "Username must contain at least 3 characters.",
                "error"
            );

            return;
        }

        if (password.length < 8) {
            setMessage(
                "Password must contain at least 8 characters.",
                "error"
            );

            return;
        }

        if (password !== confirmation) {
            setMessage(
                "Passwords do not match.",
                "error"
            );

            return;
        }

        const submitButton =
            registerForm.querySelector(
                ".submit-button"
            );

        submitButton.disabled = true;

        setMessage("Creating account...");

        try {
            const response = await fetch(
                "/api/auth/register",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    body: JSON.stringify({
                        username: username,
                        password: password,
                        confirm_password:
                            confirmation
                    })
                }
            );

            const data =
                await readJsonResponse(
                    response
                );

            if (!response.ok) {
                throw new Error(
                    getApiError(
                        data,
                        "Registration failed."
                    )
                );
            }

            registerForm.reset();

            resetPasswordAppearance(
                registerForm
            );

            loginFormTouched = false;

            clearLoginForm();

            selectAuthView("login");

            setMessage(
                "Account created successfully. Please sign in.",
                "success"
            );

            loginForm
                .elements
                .username
                .focus();

        } catch (error) {
            setMessage(
                error.message ||
                    "Unable to create account.",
                "error"
            );

        } finally {
            submitButton.disabled = false;
        }
    }
);