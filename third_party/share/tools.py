import json
import os
import sys

import click


@click.group()
def cli():
    pass


@cli.command()
def gpus():
    import torch.cuda
    click.echo(','.join(str(x) for x in range(torch.cuda.device_count())))


@cli.command()
def gpu_num():
    import torch.cuda
    click.echo(str(torch.cuda.device_count()))


@cli.command()
def tasks():
    from run_lib import read_all_contexts
    DAGContext = read_all_contexts("NkBenchmark-contexts.json")
    scenario_list = [info.run_unit.scenario_entry_point for info in DAGContext]
    new_list = [str(x.split('.')[-1]) for x in scenario_list]
    click.echo(new_list)


@cli.command
def nlp_pretrained():
    meta = get_meta()
    pretrained = meta['pretrained_model_path']
    if pretrained.startswith('./'):
        click.echo(os.path.abspath(os.path.join(os.environ['MODEL_PATH'], pretrained)))
    else:
        parts = pretrained.split('/')
        if len(parts) != 2:
            raise ValueError(f'Unknown format of pretrained model: {pretrained}')
        click.echo(pretrained)


def get_meta():
    if 'MODEL_PATH' in os.environ:
        meta_json_path = os.path.join(os.environ['MODEL_PATH'], 'meta.json')
    else:
        meta_json_path = 'meta.json'

    if not os.path.exists(meta_json_path):
        return {}

    with open(meta_json_path) as f:
        return json.load(f)


if __name__ == '__main__':
    cli()
