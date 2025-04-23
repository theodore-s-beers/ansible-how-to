import marimo

__generated_with = "0.13.1"
app = marimo.App(
    width="medium",
    app_title="Ansible How-to",
    auto_download=["html"],
)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # How we use Ansible to manage our servers

        The following is meant to be a basic, step-by-step introduction to Ansible and a guide to how our team uses it.

        - Ansible is a tool that can be set up to connect to each/all of our servers, via SSH to a sudoer account, and run various tasks according to our instructions.
        - This could include, e.g., “Log into all of our Ubuntu servers and update `apt` packages on each.”
        - In order to do this, we have Ansible run on a **control node**, i.e., a machine that can be configured to have SSH access to the hosts that are under management. This could be another server—which is how we’re currently running things—or a personal laptop or desktop machine. It doesn’t really matter, as long as access is possible. (Think: are the servers that we’re managing on the inside of a university or corporate network? If so, the control node will also need to be there, either directly or via VPN or similar.)
        - **Ansible is a Python-based tool.** That means: the tool itself is best installed via `pip` or similar (we use `uv` virtual environments, as described below); Python obviously needs to be available on the control node; and Python also needs to be installed on the managed servers.
        - Ansible is at least somewhat tolerant of differences among the Python versions on various hosts. We just make sure that none of our machines is running a severely out-of-date version. So far it has worked just fine.
        - On the control node, we have things run under a dedicated `ansible` user account. Configuration can then live in that user’s home directory.
        - There are three areas of config that are currently relevant for us: the **global Ansible config**, at `~/.ansible.cfg`; the **inventory of hosts**, which we have at `~/inventory.ini`; and the **playbooks**, i.e. the workflows that we have written to be run on the hosts, which are YAML files located in the `~/playbooks` directory.
        - For us, the Ansible core configuration is minimal and rarely, if ever, needs adjustment.
        - Our inventory of hosts changes over time (usually growing). This will be explained below.
        - Playbooks are frequently added and edited. This is where the most activity happens.

        ## Log in, get set up

        - These instructions assume that you can get logged into the `ansible` user on our control node.
        - Once there, feel free to start a new Python virtual environment from scratch: `uv venv`
        - Activate the venv: `source .venv/bin/activate`
        - Install Ansible: `uv pip install ansible`
        - You should now be able to run a playbook, e.g. the following, which just gathers some system info about each of our servers: `ansible-playbook playbooks/info.yml`
        - If it’s your first time, follow along with what Ansible is doing. It will print output as it “gathers info” about each host (i.e., ensures that it can actually access the host as specified in the inventory), then as it performs each defined task on each host.

        ### Enhancement: tmux

        - Sometimes an Ansible playbook can take a while to run, depending on what it’s doing. You may not want to be forced to sit and watch it. For this reason (and others), it’s a good idea to run playbooks in tmux sessions.
        - An introduction to tmux is out of scope here, but basically, you can: start a new tmux session; set up and/or activate the Python virtual environment; start running a playbook; and detach from the session. It will continue running in the background, and you can re-attach to it at any point.
        - tmux is cool; please consider using it in a variety of contexts, not just for Ansible.

        ## Ansible core config

        Our config is very simple, something like the following:

        ```ini
        [defaults]
        inventory = inventory.ini
        interpreter_python = auto_silent
        ```

        (The `auto_silent` value means “Try to find an appropriate Python interpreter on each host, and don’t complain about minor version differences between Python on the control node and on the various hosts.”)

        Again, this file rarely even needs to be touched.

        ## Inventory

        Our inventory of hosts is another simple INI file. (Keep in mind, we’re managing just a few dozen servers at this point. It may be that teams with more resources gradually scale into more elaborate setups.)

        Hosts are organized in groups. For each host, we define a name, the domain or IP address, the port (if not 22), and the user account on the host side that Ansible will be logging into. Here’s an example:

        ```ini
        server1 ansible_host=server1.hpc.example.edu ansible_port=9876 ansible_user=adm
        ```

        As you can imagine, Ansible would use this to run something like `ssh -p 9876 adm@server1.hpc.example.edu` under the hood.

        Here is an example of what inventory groups look like:

        ```ini
        [main_servers]
        foo ansible_host=foo.cs.example.edu ansible_port=8989 ansible_user=adm
        bar ansible_host=bar.cs.example.edu ansible_port=8989 ansible_user=adm
        baz ansible_host=baz.cs.example.edu ansible_port=8989 ansible_user=adm

        [special_cluster]
        worker1 ansible_host=worker1.hpc.example.edu ansible_port=9876 ansible_user=adm
        worker2 ansible_host=worker2.hpc.example.edu ansible_port=9876 ansible_user=adm
        worker3 ansible_host=worker3.hpc.example.edu ansible_port=9876 ansible_user=adm
        ```

        This structure is convenient because we can run playbooks on: a single host; a list of hosts; a single group; a list of groups; a mixture of groups and individual hosts; or all hosts. (At least, I _think_ all of those are possible. I regularly run playbooks on all hosts, single groups, lists of hosts, and individual hosts.)

        Examples:

        ```sh
        ansible-playbook playbooks/update.yml --limit special_cluster
        ```

        ```sh
        ansible-playbook playbooks/reboot.yml --limit baz
        ```

        You get the idea. The inventory needs to be accurate, however. This is the list of servers to which Ansible is supposed to have access, and the details that it needs to make those connections. (A separate issue is ensuring that the `ansible` user on the control node has its SSH public key added to each host. And the user account on the host side should have passwordless `sudo`. These details will be covered below.)

        ## Playbooks

        This is where the magic happens, and much could be said. But for the moment, let’s just look at a basic example playbook:

        ```yaml
        - name: Update servers
          hosts: all
          become: true
          tasks:
            - name: Update, clean up, etc.
              apt:
                update_cache: true
                cache_valid_time: 3600
                upgrade: dist
                autoremove: true
                autoclean: true
              register: apt_result
              retries: 3
              delay: 10
              until: apt_result is succeeded
        ```

        And we can step through this one line/section at a time:

        - The name of the playbook is something short and descriptive.
        - This one applies to all hosts, unless limited at the time of running the playbook (with the `--limit` option).
        - `become: true` means that Ansible will escalate privileges on the host to run these tasks, i.e., it will run with `sudo`. This option is set in most of our playbooks, since they involve system administration.
        - Here the list of tasks has only one item, but most of our playbooks have a few or several (not too many, though).
        - Since interacting with `apt` is common, Ansible has a built-in module for it. We just specify that: it should update the package cache if it’s more than an hour old; all packages will be upgraded; and `apt` will be asked to clean up after itself.
        - We store the result of each run of this task on each host. If it fails for some reason, Ansible will retry it up to 3 times, waiting 10 seconds between retries. Once the task succeeds, it’s done.

        Hopefully this is easy to understand. Some important points, though...

        - **Please be careful!** You could easily bork dozens of servers with a careless mistake in a playbook running as root.
        - Read [the docs](https://docs.ansible.com/ansible/latest/playbook_guide/); they’re quite useful.
        - Yes, LLMs can help us draft and edit playbooks—they’re quite familiar with Ansible, in fact—but I cannot emphasize enough the importance of double- and triple-checking everything and looking into the docs for any point that is unclear.
        - **Keep it simple.** This relates to the previous point: GPT might suggest a playbook to you that does something exotic, which you don’t fully understand. That’s the last thing you want to be running on a bunch of servers!
        - I recommend not trying to do too many things in a single playbook. Once you have more than a few tasks, start thinking about splitting things into multiple playbooks, if possible.

        **The bottom line is that you need to be very, very careful and meticulous.** This isn’t rocket science, but writing a new playbook or making changes to an existing one demands your full attention.

        ## Backtrack: Setting up SSH access to hosts

        As was noted above, when we declare a host in our inventory that looks like the following:

        ```ini
        foo ansible_host=foo.cs.example.edu ansible_port=8989 ansible_user=adm
        ```

        ... that corresponds to Ansible running an SSH login like so:

        ```sh
        ssh -p 8989 adm@foo.cs.example.edu
        ```

        In order for this to work, obviously, the **public key** of the `ansible` user on the control node needs to be listed among the `authorized_keys` for user `adm` (in this example) on the server at `foo.cs.example.edu`. There are various ways of getting the key placed where it needs to be (in this example, `/home/adm/.ssh/authorized_keys` on the host); suffice it to say that it needs to be done one way or another.

        A final consideration is that the Ansible user on the host side—which we’ve been calling `adm` in these examples—should have **passwordless sudo**. This will allow Ansible to escalate privileges for tasks that require it (e.g. `apt update`).

        ## Conclusion

        For members of our team who may need to interact with our Ansible setup, the process would be roughly as follows:

        - SSH into the control node
        - Switch to the `ansible` user
        - Start a tmux session, or attach to an existing one
        - Set up a Python virtual environment (with `uv`) and install Ansible, or activate an existing venv
        - Review the Ansible core config at `~/.ansible.cfg` if necessary; likewise the inventory of hosts at `~/inventory.ini`
        - Review the existing playbooks in the directory `~/playbooks`
        - Make any necessary additions or changes, **taking great care**
        - Run playbooks as appropriate, using commands of the format `ansible-playbook playbooks/info.yml`. Remember that you can add the `--limit` option to stipulate that a playbook should be run only on certain hosts (overriding the target hosts specified in the playbook YAML itself).
        - Feel free to detach from the tmux session (Ctrl+B then D); any running playbook will continue. You can then even exit your SSH session on the control node without interrupting work.
        """
    )
    return


if __name__ == "__main__":
    app.run()
